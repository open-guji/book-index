"""Adversarial checks for attaching external scans to bibliographic Works."""
import importlib.util
from pathlib import Path

import pytest

pytest.importorskip('opencc')


spec = importlib.util.spec_from_file_location('rematch_commons', Path(__file__).parents[1] / '.claude/qa/rematch_commons.py')
matcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(matcher)


@pytest.mark.parametrize('name,dynasty,raw,expected', [
    ('吴敬梓', '清', '（清）吳敬梓著', True),
    ('宋敏求', '北宋', '宋敏求撰', True),
    ('周密', '南宋', '周密撰', True),
    ('金履祥', '元', '金履祥撰', True),
    ('王修', '汉', '〔漢〕王修撰', True),
    ('王世贞', '明', '明王世貞撰', True),
    ('王世贞', '清', '〔明〕王世貞撰', False),
    ('王琮', '北宋', '〔南宋〕王琮撰', False),
    ('山谦之', '刘宋', '(南朝宋)山謙之纂修', True),
    ('山谦之', '北宋', '(南朝宋)山謙之纂修', False),
    ('王安', '宋', '王安石撰', False),
    ('敬梓', '清', '吴敬梓著', False),
    ('刘熙', '汉', '范曄撰，劉昭注', False),
    ('何晏', '魏', '〔魏〕何晏集解，〔梁〕皇侃義疏', True),
    ('皇侃', '梁', '〔魏〕何晏集解，〔梁〕皇侃義疏', True),
    ('王安石', '宋', '王〓石撰', False),
])
def test_author_boundaries_and_dynasty(name, dynasty, raw, expected):
    assert matcher.author_supported(name, dynasty, raw) is expected


def work():
    return {'id': 'test', 'type': 'work', 'title': '論語集解',
            'authors': [{'name': '何晏', 'dynasty': '魏'}]}


def scan():
    return {'book': '論語集解', 'book_categories': ['論語集解'], 'mime': 'application/pdf',
            'title': '論語集解十卷', 'author': '〔魏〕何晏集解', 'pageid': 1, 'file': '論語集解.pdf'}


def test_exact_title_does_not_override_different_author():
    w = work()
    w['authors'] = [{'name': '孫綽', 'dynasty': '晉'}]
    assert matcher.classify(w, scan())[0] == 'author_mismatch'


def test_single_file_local_evidence_is_required_for_all_contributors():
    w = work()
    w['authors'].append({'name': '皇侃', 'dynasty': '梁'})
    assert matcher.classify(w, scan())[0] == 'work_contributors_not_all_supported'


def test_composite_scan_is_never_attached_as_a_standalone_book():
    r = scan()
    r['book_categories'].append('孟子')
    assert matcher.classify(work(), r)[0] == 'multi_book_file'


def test_single_category_does_not_hide_aggregated_author_metadata():
    r = scan()
    r['author'] = '〔魏〕何晏集解 <br /> 〔漢〕趙岐撰'
    assert matcher.classify(work(), r)[0] == 'source_contributors_not_all_supported'


def test_secondary_book_titles_in_author_field_are_deferred():
    w = {'title': '周易', 'authors': [{'name': '王弼', 'dynasty': '魏'}]}
    r = {**scan(), 'title': '周易', 'book_categories': ['周易'],
         'author': '王弼, 韓康伯註. 尚書 / 孔氏傳. 毛詩 / 毛亨傳 ; 鄭玄箋'}
    assert matcher.classify(w, r)[0] == 'source_contributors_not_all_supported'


def test_aggregated_category_does_not_override_file_title():
    r = scan()
    r['title'] = '論語集解義疏'
    assert matcher.classify(work(), r)[0] == 'file_title_conflict'


def test_lost_original_does_not_receive_extant_homonym_scan():
    w = work()
    w['loss_status'] = 'lost'
    assert matcher.classify(w, scan())[0] == 'lost_work_conflict'


def test_missing_author_is_deferred_not_title_matched():
    r = scan()
    r.pop('author')
    assert matcher.classify(work(), r)[0] == 'file_author_unusable'


def test_volume_count_is_not_a_different_title():
    assert matcher.classify(work(), scan())[0] == 'confirmed'


def test_preface_only_scan_is_deferred_even_with_matching_author():
    r = scan()
    r['volume'] = '卷首'
    assert matcher.classify(work(), r)[0] == 'front_matter_only'


def test_chinese_first_volume_precedes_shorter_later_volume_filename():
    first = {**scan(), 'file': 'long name 卷一.pdf', 'volume': '卷一', 'pageid': 2}
    second = {**scan(), 'file': '卷二.pdf', 'volume': '卷二', 'pageid': 1}
    assert matcher.rank(first) > matcher.rank(second)


def test_existing_commons_domain_is_detected_despite_custom_resource_id():
    assert matcher.has_commons({'resources': [{'id': 'custom', 'url': 'https://commons.wikimedia.org/wiki/File:X.pdf'}]})
