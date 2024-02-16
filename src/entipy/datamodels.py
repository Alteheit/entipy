import json
import typing as t
import math
import itertools
from sortedcontainers import SortedSet

id_seq = itertools.count(0)

class Reference:
    oid: int # Reference ObjectID, used for caching/indexing.
    field_names: SortedSet[str] # Caching for use in compare
    metadata: str # JSON-dumps-ed dictionary. No such thing as frozendict in Python by default.
    def __init__(self, **kwargs):
        # Metaprogramming to instantiate Field inheritors
        # from values passed as kwargs
        self.oid = next(id_seq)
        self.field_names = SortedSet()
        for k, v in kwargs.items():
            if k == 'metadata':
                self.metadata = json.dumps(v)
                continue
            field_class = getattr(self, k)
            field_instance = field_class(v)
            setattr(self, k, field_instance)
            self.field_names.add(k)
    def _fellegi_sunter_adjustment(self,
        eq: bool,
        true_match_probability: float,
        false_match_probability: float
    ):
        """The logarithmic Fellegi-Sunter adjustment for a boolean similarity."""
        if eq:
            return math.log(true_match_probability / false_match_probability)
        return math.log(
            (1 - true_match_probability) / (1 - false_match_probability)
        )
    def compare(self, other):
        score = 0
        for field_name in self.field_names:
            self_field = getattr(self, field_name)
            other_field = getattr(other, field_name)
            # Need to implement nil-skipping here because
            # the users can't be expected to implement it in
            # their Field comparison function
            if (self_field.value is None) or (other_field.value is None):
                continue
            field_match = self_field.compare(other_field)
            field_score = self._fellegi_sunter_adjustment(
                field_match,
                self_field.true_match_probability,
                self_field.false_match_probability,
            )
            score += field_score
        return field_score
    def as_json(self, include_metadata=False):
        """Returns self as normal JSON."""
        representation = {}
        for field_name in self.field_names:
            self_field = getattr(self, field_name)
            representation.update({
                field_name: self_field.value
            })
        if include_metadata:
            representation.update({'metadata': self.metadata})
        return representation
    # Hash compliance based on oid
    def __lt__(self, other):
        return self.oid < other.oid
    def __le__(self, other):
        return self.oid <= other.oid
    def __gt__(self, other):
        return self.oid > other.oid
    def __ge__(self, other):
        return self.oid >= other.oid
    def __eq__(self, other):
        return self.oid == other.oid
    def __ne__(self, other):
        return self.oid != other.oid
    def __hash__(self):
        return hash(self.oid)
    def __repr__(self):
        return f'''<{type(self).__name__} fields={[f"{field_name}: {getattr(self, field_name).value}" for field_name in self.field_names]}>'''.replace("'", "")

class Field:
    value: t.Hashable
    true_match_probability: float = 0.9
    false_match_probability: float = 0.1
    # Hash compliance based on value
    def __init__(self, value):
        self.value = value
    def compare(self, other):
        return self.value == other.value
    def __lt__(self, other):
        return self.value < other.value
    def __le__(self, other):
        return self.value <= other.value
    def __gt__(self, other):
        return self.value > other.value
    def __ge__(self, other):
        return self.value >= other.value
    def __eq__(self, other):
        return self.value == other.value
    def __ne__(self, other):
        return self.value != other.value
    def __hash__(self):
        return hash(self.value)
    def __repr__(self):
        return f'''<{type(self).__name__} value={self.value}>'''

class Cluster:
    oid: int # Cluster ObjectID, used for caching/indexing.
    references: set[Reference]
    def __init__(self, references: set[Reference]):
        self.oid = next(id_seq)
        self.references = references
    def compare(self, other):
        score = 0
        for ref_1 in self.references:
            for ref_2 in other.references:
                score += ref_1.compare(ref_2)
        return score
    def weightsum(self, other):
        score = 0
        for ref_1 in self.references:
            for ref_2 in other.references:
                score += ref_1.compare(ref_2)
        return max(0, score)
    def merge(self, other):
        return Cluster(self.references.union(other.references))
    def as_json(self, include_reference_metadata=False):
        """Returns the cluster as a list of dictionaries.
        Each element in the list is one of the References.
        Not a set because dictionaries aren't hashable."""
        representation = []
        for reference in self.references:
            representation.append(reference.as_json(include_metadata=include_reference_metadata))
        return representation
    def __repr__(self):
        return f'''<Cluster id={self.oid} refcount={len(self.references)}>'''

class Pair:
    cluster_oid_1: int # Ref, not val, for performance
    cluster_oid_2: int # Ref, not val, for performance
    possible_improvement: float
    def __init__(self, cluster_oid_1: int, cluster_oid_2: int, possible_improvement: float):
        self.cluster_oid_1 = min(cluster_oid_1, cluster_oid_2)
        self.cluster_oid_2 = max(cluster_oid_1, cluster_oid_2)
        self.possible_improvement = possible_improvement
    # Hash and comp implementations for SortedSet usage
    def __hash__(self):
        return hash((self.cluster_oid_1, self.cluster_oid_2, self.possible_improvement))
    def __eq__(self, other):
        if not isinstance(other, Pair): return False
        return all([
            self.cluster_oid_1 == other.cluster_oid_1,
            self.cluster_oid_2 == other.cluster_oid_2,
            self.possible_improvement == other.possible_improvement,
        ])
    def __ne__(self, other):
        if not isinstance(other, Pair): return True
        return any([
            self.cluster_oid_1 != other.cluster_oid_1,
            self.cluster_oid_2 != other.cluster_oid_2,
            self.possible_improvement != other.possible_improvement,
        ])
    def __lt__(self, other):
        return self.possible_improvement < other.possible_improvement
    def __gt__(self, other):
        return self.possible_improvement > other.possible_improvement
    def __le__(self, other):
        return self.possible_improvement <= other.possible_improvement
    def __ge__(self, other):
        return self.possible_improvement >= other.possible_improvement
