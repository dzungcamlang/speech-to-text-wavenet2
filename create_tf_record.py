import os
import pickle
import glog
import utils
import tensorflow as tf

flags = tf.app.flags
flags.DEFINE_string('input_dir', 'f:/speech', 'Directory to mmc dataset.')
flags.DEFINE_string('list_path', 'data/list.pkl', 'Path to list.')
flags.DEFINE_integer('train_test_ratio', 10, 'The ratio of train to test.')
flags.DEFINE_string('output_dir', 'data', 'Path of output.')
FLAGS = flags.FLAGS


def _read_vctk(root, ratio=10):
  ids = []
  for line in open(root + '/VCTK-Corpus/speaker-info.txt', 'r').readlines()[1:]:
    ids.append('/p' + line.split(' ')[0])
  train_filenames = []
  test_filenames = []
  for i, id in enumerate(ids):
    wav_dir = '/VCTK-Corpus/wav48' + id
    txt_dir = '/VCTK-Corpus/txt' + id
    for filename in os.listdir(root + wav_dir):
      stem, ext = os.path.splitext(filename)
      if ext == '.wav':
        wav_name = wav_dir + '/' + filename
        txt_name = txt_dir + '/' + stem + '.txt'
        if os.path.exists(root + txt_name):
          if i % ratio == 0:
            test_filenames.append((wav_name, txt_name))
          else:
            train_filenames.append((wav_name, txt_name))
        else:
          glog.warning("Skip %s, the label file is not found." % filename)
  return train_filenames, test_filenames


def _create_dataset(input_dir, filenames, output_path):
  count = 0
  writer = tf.python_io.TFRecordWriter(output_path)
  for i, filename in enumerate(filenames):
    wave_path = input_dir + filename[0]
    txt_path = input_dir + filename[1]
    stem = os.path.splitext(os.path.split(filename[0])[-1])[0]
    wave = utils.read_wave(wave_path)
    label = utils.read_txt(txt_path)
    if len(wave) > len(label):
      max_wave = max(max_wave, len(wave))
      max_label = max(max_label, len(label))
      data = tf.train.Example(features=tf.train.Features(feature={
        'uid': tf.train.Feature(bytes_list=tf.train.BytesList(value=[stem.encode('utf-8')])),
        'wave/data': tf.train.Feature(float_list=tf.train.FloatList(value=wave.reshape([-1]).tolist())),
        'wave/shape': tf.train.Feature(int64_list=tf.train.Int64List(value=wave.shape)),
        'label': tf.train.Feature(int64_list=tf.train.Int64List(value=label))}))
      writer.write(data.SerializeToString())

    count = i + 1
    if count % 1000 == 0:
      glog.info('processed %d/%d files.' % (count, len(filenames)))
  if count % 1000 != 0:
    glog.info('processed %d/%d files.' % (count, len(filenames)))


def main(_):
  if os.path.exists(FLAGS.list_path):
    train_filenames, test_filenames = pickle.load(open(FLAGS.list_path, 'rb'))
  else:
    train_filenames = []
    test_filenames = []
    for dataset_name in os.listdir(FLAGS.input_dir):
      if dataset_name == 'VCTK-Corpus':
        dataset = _read_vctk(FLAGS.input_dir, FLAGS.train_test_ratio)
      else:
        glog.warning('Dataset named %s is not supported now.')
        continue
      train_filenames += dataset[0]
      test_filenames += dataset[1]
    pickle.dump((train_filenames, test_filenames), open(FLAGS.list_path, 'wb'))
  train_path = FLAGS.output_dir + '/train.record'
  test_path = FLAGS.output_dir + '/test.record'
  if not os.path.exists(FLAGS.output_dir):
    os.makedirs(FLAGS.output_dir)
  glog.info('processing train dataset...')
  _create_dataset(FLAGS.input_dir, train_filenames, train_path)
  glog.info('processing test dataset...')
  _create_dataset(FLAGS.input_dir, test_filenames, test_path)


if __name__ == '__main__':
  tf.app.run()
