"""schema-landed-check.sh readers（V4）对 has_*／_has_* 的判法：现行派生键 _has_* 单读为绿；无下划线读派生文档、双读为红。"""
import pathlib, subprocess

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'schema-landed-check.sh'


def _git_repo(path, files):
    path.mkdir(parents=True)
    subprocess.run(['git', 'init', '-q', str(path)], check=True)
    for name, text in files.items():
        f = path / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding='utf-8')
    subprocess.run(['git', '-C', str(path), 'add', '-A'], check=True)


def _readers(tmp_path, web_line):
    _git_repo(tmp_path / 'bim', {'x.py': 'pass\n'})
    _git_repo(tmp_path / 'web', {'ops/a.mjs': web_line + '\n'})
    out = tmp_path / 'out'
    r = subprocess.run(['bash', str(SCRIPT), 'readers'], capture_output=True, text=True,
                       env={'PATH': '/usr/bin:/bin:/usr/local/bin', 'BIM': str(tmp_path / 'bim'),
                            'WEB': str(tmp_path / 'web'), 'OUT': str(out)})
    return r.returncode, (out / 'V4-readers.log').read_text(encoding='utf-8')


def test_current_underscore_key_alone_is_green(tmp_path):
    rc, log = _readers(tmp_path, 'if (doc._has_text === true) n++;')
    assert rc == 0, log


def test_plain_has_read_on_derived_doc_is_red(tmp_path):
    rc, log = _readers(tmp_path, 'if (doc.has_text === true) n++;')
    assert rc == 1 and 'a.mjs:1' in log


def test_dual_read_is_red(tmp_path):
    rc, log = _readers(tmp_path, 'if (e.has_text || e._has_text) n++;')
    assert rc == 1 and 'a.mjs:1' in log


def test_retired_full_text_key_is_red(tmp_path):
    rc, log = _readers(tmp_path, "if (d['_has_full_text']) n++;")
    assert rc == 1 and 'a.mjs:1' in log
