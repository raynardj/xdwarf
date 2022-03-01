from xdwarf import Dwarf
from xdwarf import Treasure


dwarf = Dwarf.from_glob("./data/*.xml", "PMC",2)

dwarf.find_one('article-meta > article-id[pub-id-type=pmid]' , "pmid")
dwarf.find_one("abstract", "abstract").find_many("p", "paragraph")
reference = dwarf.find_one("ref-list", "ref_list").find_many("ref","reference")
reference.find_one("pub-id[pub-id-type=pmid]", "ref_id")
reference.find_one("pub-id[pub-id-type=doi]", "doi")
ref_name = reference.find_many("name", "ref_name")
ref_name.find_one("surname", "ref_surname")

dwarf.set_necessary("pmid")
dwarf.create_children()

result = dwarf()

def test_layer1():
    df1 = result.child_df()
    assert len(df1)==156

def test_layer1_col():
    df1 = result.child_df()
    for col1, col2 in zip(
        list(df1.columns),
        ["p_idx","DWARF MINED ROOT","pmid","abstract","ref_list"]):
        assert col1==col2

def test_layer2():
    df2 = result['ref_list'].child_df()
    assert len(df2)==156

def test_layer2_col():
    df2 = result['ref_list'].child_df()
    for col1, col2 in zip(
        list(df2.columns),
        ["p_idx","ref_list","reference"]):
        assert col1==col2

def test_layer3():
    df3 = result['ref_list']['reference'].child_df()
    assert len(df3)==893

def test_layer3_col():
    df2 = result['ref_list']['reference'].child_df()
    for col1, col2 in zip(
        list(df2.columns),
        ["p_idx","reference", "ref_id","doi","ref_name"]):
        assert col1==col2