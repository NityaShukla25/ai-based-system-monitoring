from static_collector import get_or_create_host
from feature_builder import build_training_features

host_id = get_or_create_host()

build_training_features(host_id)
