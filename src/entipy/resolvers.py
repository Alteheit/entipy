import typing as t
from sortedcontainers import SortedSet
from .datamodels import Reference, Cluster, Pair

class SerialResolver:
    """The single-threaded object that resolves References."""
    # Internal object state
    references: list[Reference] # A list/queue of References to resolve
    clusters = list[Cluster] # The list of Clusters to resolve. NOT the main database! This is basically a queue of clusters to add to cluster_map.
    cluster_map = dict # The main database of Clusters; {oid: cluster}
    pair_set: SortedSet[Pair] # Priority queue for cluster_stream
    candidate_set: SortedSet[Pair] # Priority queue for cluster_pass and cluster_solve
    cluster_pairs: dict # Index for cluster_stream to remove pairs from pair_set and candidate_set; {oid: set[Pair]}
    def __init__(self, references):
        # Internal object state init
        self.references = list(references)
        self.cluster_map = {}
        self.pair_set = SortedSet()
        self.candidate_set = SortedSet()
        self.cluster_pairs = {}
    def _construct_pair_set(self):
        """Builds the pair set from the cluster map.
        Used when there are no pairs in the pair set."""
        for cluster_oid_1, cluster_1 in self.cluster_map.items():
            for cluster_oid_2, cluster_2 in self.cluster_map.items():
                if cluster_oid_1 >= cluster_oid_2: continue
                pair_weightsum = cluster_1.weightsum(cluster_2)
                pair = Pair(cluster_oid_1, cluster_oid_2, pair_weightsum)
                self.pair_set.add(pair)
                # Add the pair to the cluster pairs
                if not self.cluster_pairs.get(cluster_oid_1):
                    self.cluster_pairs.update({
                        cluster_oid_1: set([pair])
                    })
                else:
                    self.cluster_pairs.get(cluster_oid_1).add(pair)
                if not self.cluster_pairs.get(cluster_oid_2):
                    self.cluster_pairs.update({
                        cluster_oid_2: set([pair])
                    })
                else:
                    self.cluster_pairs.get(cluster_oid_2).add(pair)
    def _cluster_pass(self, cluster_map: dict) -> t.Tuple[dict, bool]:
        '''Merges the two most similar clusters, if any.
        If there are no similar clusters, does nothing.

        In practice, this function is expected to only run on
            two clusters at a time, so this is why we do not
            use pervasive non-pessimization here.

        Mutates its inputs!
        Is not meant to mutate the state of the executor.

        Parameters
        ----------
        cluster_map: dict
            The database of clusters. Structure: {oid: cluster}
            Notably, NOT the executor's cluster_map.

        Returns
        -------
        dict
            The new cluster_map
        bool
            Whether the cluster_map is already optimal.
            True if it is, False if it is not.
        '''
        candidates: SortedSet[Pair] = SortedSet()
        for oid_1, cluster_1 in cluster_map.items():
            for oid_2, cluster_2 in cluster_map.items():
                if oid_1 >= oid_2: continue
                weightsum = cluster_1.weightsum(cluster_2)
                if weightsum <= 0: continue
                pair = Pair(oid_1, oid_2, weightsum)
                candidates.add(pair)
        if not candidates: return (cluster_map, True)
        # Merge the clusters in the best pair
        # Remove the old clusters from the cluster map
        # Add the merged cluster to the cluster map
        best_pair: Pair = candidates.pop()
        oid_1 = best_pair.cluster_oid_1
        oid_2 = best_pair.cluster_oid_2
        cluster_1 = cluster_map[oid_1]
        cluster_2 = cluster_map[oid_2]
        merged_cluster = cluster_1.merge(cluster_2)
        merged_oid = merged_cluster.oid
        del cluster_map[oid_1]
        del cluster_map[oid_2]
        cluster_map[merged_oid] = merged_cluster
        return (cluster_map, False)
    def _cluster_solve(self, cluster_map: dict) -> t.Tuple[dict, bool]:
        """Solves the cluster_map to completion.
        Stops when there are no longer any possible improvements.

        Mutates its inputs!
        Is not meant to mutate the state of the executor.

        Parameters
        ----------
        cluster_map: dict
            The database of clusters. Structure: {oid: cluster}
            Notably, NOT the executor's cluster_map.

        Returns
        -------
        dict
            The cluster_map, solved to completion
        bool
            Whether the cluster_map was changed"""
        changed = False
        while True:
            cluster_map, is_optimal = self._cluster_pass(cluster_map)
            if is_optimal: break
            changed = True
        return (cluster_map, changed)
    def _cluster_stream(self, new_observations: Reference | Cluster, cluster_map: dict) -> dict:
        """Pops a reference from the references list,
        then adds the reference to the cluster database and solves the database
        to its heuristic completion.

        Mutates its inputs!
        Is not meant to mutate the state of the executor.

        Parameters
        ----------
        reference: Reference
            The new reference to add to the cluster_map.
            Will be turned into a cluster.
        cluster_map: dict
            The database of clusters. Structure: {oid: cluster}

        Returns
        -------
        dict
            The cluster_map, solved to completion, including the new reference
        """
        # Setup
        active_clusters = {} # {oid: cluster}
        # Generate a new cluster from the new_observations and add it to cluster_map
        if isinstance(new_observations, Reference):
            new_cluster = Cluster(set([new_observations]))
        elif isinstance(new_observations, Cluster): # Probably not needed in EntiPy 0.0.1?
            new_cluster = Cluster(new_observations.references)
        new_oid = new_cluster.oid
        cluster_map[new_oid] = new_cluster
        active_clusters[new_oid] = new_cluster
        # The completion loop
        while True:
            # Calculate weightsum for all (cluster_1, cluster_2)
            #  such that either cluster_1 or cluster_2 is active
            pair_set: SortedSet[Pair] = SortedSet() # There's a pair_set property on the executor, but I guess we're using this one?
            for active_oid, active_cluster in active_clusters.items():
                for oid, cluster in cluster_map.items():
                    if active_oid == oid: continue
                    weightsum = active_cluster.weightsum(cluster)
                    if weightsum <= 0: continue
                    pair = Pair(active_oid, oid, weightsum)
                    pair_set.add(pair)
            # Wipe active clusters
            active_clusters = {}
            # If there are no valid pairs, exit completion loop
            if not pair_set: break
            # Pop the best pair and solve it
            best_pair: Pair = pair_set.pop()
            cluster_oid_1 = best_pair.cluster_oid_1
            cluster_oid_2 = best_pair.cluster_oid_2
            cluster_1 = cluster_map.get(cluster_oid_1)
            cluster_2 = cluster_map.get(cluster_oid_2)
            local_cluster_map = {
                cluster_oid_1: cluster_1,
                cluster_oid_2: cluster_2,
            }
            solution, _ = self._cluster_solve(local_cluster_map) # Oh, this is why cluster_pass and cluster_solve need to be pure.
            # Add new entities to the cluster_map and active_clusters
            for oid, cluster in solution.items():
                if cluster_map.get(oid): continue
                cluster_map[oid] = cluster
                active_clusters[oid] = cluster
            # Remove cluster_1 and cluster_2 if solution excludes them
            if not solution.get(cluster_oid_1):
                del cluster_map[cluster_oid_1]
            if not solution.get(cluster_oid_2):
                del cluster_map[cluster_oid_2]
        # Return the completed cluster_map
        return cluster_map
    def resolve(self, verbose: bool = False) -> None:
        """Drains every Reference in the references list.
        Includes every Reference in the cluster_map and resolves cluster_map."""
        for i, reference in enumerate(self.references):
            if verbose:
                print(f'''Resolving:{i + 1}/{len(self.references)}:{reference}''')
            self.cluster_map = self._cluster_stream(reference, self.cluster_map)
        self.references = []
    def add(self, new_observation: Reference | list[Reference]) -> None:
        """Adds reference(s) to the references list."""
        if type(new_observation) == list:
            self.references.extend(new_observation)
        else:
            self.references.append(new_observation)
    def retrieve_clusters(self, include_reference_metadata=False):
        """Getter for clusters."""
        return {
            oid: cluster.as_json(include_reference_metadata=include_reference_metadata)
            for oid, cluster in self.cluster_map.items()
        }
