"""统一配置：代码在仓库里，所有数据（引擎、数据集、模型、人物库、日志、校准状态）都在 XUAN_HOME。
XUAN_HOME 默认 ~/.local/share/<项目名>；XUAN_PUBLIC 默认 1（公开模式：不显示置信标签、过滤出处、结论末尾加「仅供参考」）。"""
import os, sys
from project import PROJECT, FOOTER
CODE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(CODE)
HOME = os.path.abspath(os.path.expanduser(os.environ.get('XUAN_HOME') or os.path.join('~', '.local', 'share', PROJECT)))
ENGINE = os.environ.get('XUAN_ENGINE') or os.path.join(HOME, 'engine')
DATASET = os.path.join(HOME, 'dataset', 'v4')
MODELS = os.environ.get('XUAN_MODELS') or os.path.join(HOME, 'models')
EVAL = os.path.join(HOME, 'eval')
TRAIN_WORK = os.path.join(HOME, 'train')
PEOPLE = os.environ.get('XUAN_PEOPLE') or os.path.join(HOME, 'people.json')
LOGS = os.path.join(HOME, 'logs')
CALIB = os.path.join(HOME, 'calib_state.json')
PY = sys.executable
TSX = os.path.join(ENGINE, 'node_modules', '.bin', 'tsx')
PUBLIC = os.environ.get('XUAN_PUBLIC', '1') != '0'
LOCK = os.path.join(ROOT, 'engine.lock')
CALIB_METHODS = ['bugua', 'fengshui', 'xiangfa', 'cezi', 'yunxian']
LOG_METHODS = CALIB_METHODS + ['hepan', 'natal']
os.environ.setdefault('XUAN_ENGINE', ENGINE); os.environ.setdefault('XUAN_MODELS', MODELS)
def env():
    return {**os.environ, 'XUAN_ENGINE': ENGINE, 'XUAN_MODELS': MODELS, 'XUAN_HOME': HOME, 'BS': 'XD2'}
def lock():
    d = {}
    for l in open(LOCK):
        l = l.strip()
        if l and not l.startswith('#') and '=' in l: k, v = l.split('=', 1); d[k.strip()] = v.strip()
    return d
