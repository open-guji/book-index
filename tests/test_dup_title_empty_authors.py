"""Regression for §二·2: two works with same title but no authors must not be grouped as duplicate."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / ".claude/qa"))
import scan

def test_empty_authors_not_grouped():
    works = {
        'id1': {'id':'id1','title':'同題','authors':[],'merged_into':None,'indexed_by':[]},
        'id2': {'id':'id2','title':'同題','authors':[],'merged_into':None,'indexed_by':[]},
        'id3': {'id':'id3','title':'同題','authors':[{'name':'甲'}],'merged_into':None,'indexed_by':[]},
        'id4': {'id':'id4','title':'同題','authors':[{'name':'甲'}],'merged_into':None,'indexed_by':[]},
    }
    IW={'id1':{'period':'song'},'id2':{'period':'song'},'id3':{'period':'song'},'id4':{'period':'song'}}
    R=scan.run_checks(works, IW, {}, {}, {}, {})
    ids=set(r['id'] for r in R.get('I',[]))
    assert 'id1' not in ids and 'id2' not in ids, "empty authors must not be in I"
    assert 'id3' in ids and 'id4' in ids

if __name__=='__main__':
    test_empty_authors_not_grouped()
    print("PASS")
