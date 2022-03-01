from rust_dwarf import Dwarf as RustDwarf
from rust_dwarf import DeepVec
import pandas as pd
import numpy as np
from typing import List

tab = "\t"


class FieldTrait:
    """
    Class used as abstract trait for all Field and Dwarf
    """

    def check_sibling(self, name):
        for sibling in self.children:
            if sibling.name == name:
                raise ValueError(f"{name} existed")

    def append_one(self, query, name, many):
        parent_chain = [] if self.root_dwarf else self.name_chain+[self.name]
        new_field = Field(query, name, many, parent_chain)
        new_field.dwarf = self.dwarf
        new_field.parent = self
        self.children.append(
            new_field
        )
        return new_field

    def find_one(self, query, name):
        return self.append_one(query, name, False)

    def find_many(self, query, name):
        return self.append_one(query, name, True)

    def create_children(self):
        for child in self.children:
            child.create_all()


class Field(FieldTrait):
    """
    A wrap around the XMLField class in rust
    """

    def __init__(
        self, query: str, name: str, many: bool, name_chain: List[str] = []
    ):
        self.root_dwarf = False
        self.name_chain = name_chain
        self.query = query
        self.name = name
        self.many = many  # find all or find many
        self.necessary = False
        self.children = []
        self.parent = None
        self.created = False

    def create(self,):
        if self.created:
            return

        self.dwarf.append_new_field(
            self.name_chain,
            self.query,
            self.name,
            self.necessary,
            self.many,
        )
        self.created = True

    def create_all(self):
        self.create()
        self.create_children()

    def __repr__(self, ):
        return str(self)

    def __str__(self):
        return f"Dwarf Field <{self.name}>"


class Treasure:
    """
    A wrap around the DeepVec class in rust
    # To see return result of child fields in a dataframe
    >>> Treasure.child_df()
    """

    def __init__(self, deepvec):
        self.deepvec = deepvec
        self.is_all = deepvec.is_all
        self.index = deepvec.index
        self.name = deepvec.name

    def __str__(self):
        return str(self.deepvec)

    def __repr__(self):
        return str(self)

    def get_data(self):
        return self.deepvec.get_data()

    @property
    def df(self) -> pd.DataFrame:
        df = pd.DataFrame(
            pd.Series(self.deepvec.index, name=f'p_idx'),
        )
        df[self.deepvec.name] = self.deepvec.get_data()
        return df

    @property
    def children(self):
        return list(Treasure(d) for d in self.deepvec.deep)

    @staticmethod
    def print_all(deepvec, level=0):
        print(f"{tab*level}{deepvec},(m{max(deepvec.index)})")
        for d in deepvec.deep:
            Treasure.print_all(d, level+1)

    def get_deep(self,):
        return self.deepvec.get_data()

    def analyze(self,):
        return self.print_all(self.deepvec)

    def child_df(self):
        rt = self.df
        for child in self.children:
            if child.is_all:
                col = np.array([None, ]*len(rt))
                col_fill = child.df.groupby('p_idx').agg(list)
                col[col_fill.index] = col_fill[child.name]
                rt[child.name] = col
            else:
                rt[child.name] = child.get_data()
        return rt

    def __getitem__(self, name: str):
        for i in self.children:
            if i.name == name:
                return i
        raise KeyError(f"Child name '{name}' not found")


class Dwarf(FieldTrait):
    """
    Dwarf: is pretty good at mining, in this case XML/HTML file
    This is the python API to the Rust mining tool
    >>> dwarf = Dwarf.from_glob("/GCI/data/pmc_xml/PMC003xxxxxx/PMC31*.xml", "PMC",20)

    # set the fields you want to ming
    # with xpath like API
    >>> dwarf.find_one('article-meta > article-id[pub-id-type=pmid]' , "pmid")
    >>> dwarf.find_one("abstract", "abstract").find_many("p", "paragraph")
    >>> reference = dwarf.find_one("ref-list", "ref_list").find_many("ref","reference")
    >>> reference.find_one("pub-id[pub-id-type=pmid]", "ref_id")
    >>> reference.find_one("pub-id[pub-id-type=doi]", "doi")
    >>> ref_name = reference.find_many("name", "ref_name")
    >>> ref_name.find_one("surname", "ref_surname")

    # set necessary field for mining
    >>> dwarf.set_necessary("pmid")

    # start the mining
    >>> result = dwarf()
    """

    def __init__(self, path_list: List[str], name: str, num_threads: int = -1):
        """
        - path_list: List[str]: A list of XML file
        - name: str:  name of this project
        - num_threads: int : number of threads we'll be using
            use 0 for all
            use neg number for all - n
        """
        self.root_dwarf = True
        self.num_threads = self.real_threads(num_threads)
        self.path_list = path_list
        self.name = name
        self.dwarf = RustDwarf(path_list, name, num_threads)
        self.children = []

    @classmethod
    def from_glob(cls, glob_pattern: str, name: str, num_threads: int = -1):
        """
        Start dwarf from a glob pattern
        - glob_pattern: str, the glob pattern to find a list of XML/HTML files
        - name: str, 
        - num_threads: int = -1
            use 0 for all
            use neg number for all - n
        """
        num_threads = cls.real_threads(num_threads)
        obj = cls([], name, num_threads)
        obj.dwarf = RustDwarf.from_glob(glob_pattern, name, num_threads)
        obj.path_list = obj.dwarf.path_list
        return obj

    @staticmethod
    def real_threads(num_threads) -> int:
        if num_threads < 1:
            import multiprocessing
            total = multiprocessing.cpu_count()
            new = total - num_threads
            if new > 0:
                return new
            raise ValueError(
                f"You have CPU:{total}, but you are put in {num_threads}")
        else:
            return num_threads

    def set_necessary(self, name: str) -> None:
        """
        only 1 field gets to be necessary

        only direct child of a dwarf
        """
        for child in self.children:
            if child.name == name:
                child.necessary = True
            else:
                child.necessary = False

    def __call__(self) -> Treasure:
        """
        Start the mining
        """
        self.create_children()
        return Treasure(self.dwarf.mine())

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"{self.name}\n{self.dwarf}"
