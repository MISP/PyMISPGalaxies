#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from json import JSONEncoder
import os
import sys
from collections.abc import Mapping
from glob import glob
import re
from typing import List, Dict, Optional, Any, Tuple, Iterator, overload, Union

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

try:
    import jsonschema  # type: ignore
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


class EncodeGalaxies(JSONEncoder):
    def default(self, obj: Any) -> Dict[str, str]:
        if isinstance(obj, Galaxy):
            return obj.to_dict()
        return JSONEncoder.default(self, obj)


class EncodeClusters(JSONEncoder):
    def default(self, obj: Any) -> Dict[str, str]:
        if isinstance(obj, (Cluster, ClusterValue, ClusterValueMeta)):
            return obj.to_dict()
        return JSONEncoder.default(self, obj)


class PyMISPGalaxiesError(Exception):
    def __init__(self, message: str):
        super(PyMISPGalaxiesError, self).__init__(message)
        self.message = message


class UnableToRevertMachinetag(PyMISPGalaxiesError):
    pass


class Galaxy():
    """
    Represents a galaxy in the PyMISPGalaxies library.

    Attributes:
        galaxy (Dict[str, str]): The dictionary containing the galaxy data.
        type (str): The type of the galaxy.
        name (str): The name of the galaxy.
        icon (str): The icon of the galaxy.
        description (str): The description of the galaxy.
        version (str): The version of the galaxy.
        uuid (str): The UUID of the galaxy.
        namespace (str, optional): The namespace of the galaxy.
        kill_chain_order (str, optional): The kill chain order of the galaxy.
    """

    def __init__(self, galaxy: Union[str, Dict[str, str]]):
        """
        Initializes a Galaxy object from an existing galaxy.

        Args:
            galaxy (str): The name of the existing galaxy to load from the data folder.
            galaxy (Dict[str, str]): The dictionary containing the galaxy data.
        """
        if isinstance(galaxy, str):
            root_dir_galaxies = os.path.join(os.path.abspath(os.path.dirname(sys.modules['pymispgalaxies'].__file__)), 'data', 'misp-galaxy', 'galaxies')  # type: ignore [type-var, arg-type]
            galaxy_file = os.path.join(root_dir_galaxies, f"{galaxy}.json")
            with open(galaxy_file, 'r') as f:
                self.galaxy = json.load(f)
        else:
            self.galaxy = galaxy
        self.type = self.galaxy['type']
        self.name = self.galaxy['name']
        self.icon = self.galaxy['icon']
        self.description = self.galaxy['description']
        self.version = self.galaxy['version']
        self.uuid = self.galaxy['uuid']
        self.namespace = self.galaxy.pop('namespace', None)
        self.kill_chain_order = self.galaxy.pop('kill_chain_order', None)

    def save(self, file_name: str) -> None:
        """
        Saves the galaxy to a file <file_name>.json

        Args:
            file_name (str): The name of the file to save the galaxy to.
        """
        root_dir_galaxies = os.path.join(os.path.abspath(os.path.dirname(sys.modules['pymispgalaxies'].__file__)), 'data', 'misp-galaxy', 'galaxies')  # type: ignore [type-var, arg-type]
        galaxy_file = os.path.join(root_dir_galaxies, f"{file_name}.json")
        with open(galaxy_file, 'w') as f:
            json.dump(self, f, cls=EncodeGalaxies, indent=2, sort_keys=True, ensure_ascii=False)
            f.write('\n')  # needed for the beauty and to be compliant with jq_all_the_things

    def to_json(self) -> str:
        """
        Converts the galaxy object to a JSON string.

        Returns:
            str: The JSON representation of the galaxy object.
        """
        return json.dumps(self, cls=EncodeGalaxies)

    def to_dict(self) -> Dict[str, str]:
        """
        Converts the galaxy object to a dictionary.

        Returns:
            Dict[str, str]: The dictionary representation of the galaxy object.
        """
        to_return = {'type': self.type, 'name': self.name, 'description': self.description,
                     'version': self.version, 'uuid': self.uuid, 'icon': self.icon}
        if self.namespace:
            to_return['namespace'] = self.namespace
        if self.kill_chain_order:
            to_return['kill_chain_order'] = self.kill_chain_order
        return to_return


class Galaxies(Mapping):  # type: ignore
    """
    A class representing a collection of MISP galaxies.

    Parameters:
    - galaxies: A list of dictionaries representing the galaxies. Each dictionary should contain the type and other properties of a galaxy.
                If left empty, the galaxies are loaded from the data folder.

    Attributes:
    - galaxies: A dictionary containing the galaxies, where the keys are the types of the galaxies and the values are instances of the Galaxy class.
    - root_dir_galaxies: The root directory of the MISP galaxies.

    Methods:
    - validate_with_schema: Validates the galaxies against the schema.
    - __getitem__: Returns the galaxy with the specified type.
    - __iter__: Returns an iterator over the galaxy types.
    - __len__: Returns the number of galaxies in the collection.
    """

    def __init__(self, galaxies: List[Dict[str, str]] = []):
        """
        Initializes a new instance of the Galaxies class.

        Parameters:
        - galaxies: A list of dictionaries representing the galaxies. Each dictionary should contain the type and other properties of a galaxy.
                    If left empty, the galaxies are loaded from the data folder.
        """
        if not galaxies:
            galaxies = []
            self.root_dir_galaxies = os.path.join(os.path.abspath(os.path.dirname(sys.modules['pymispgalaxies'].__file__)),  # type: ignore
                                                  'data', 'misp-galaxy', 'galaxies')
            for galaxy_file in glob(os.path.join(self.root_dir_galaxies, '*.json')):
                with open(galaxy_file, 'r') as f:
                    galaxies.append(json.load(f))

        self.galaxies = {}
        for galaxy in galaxies:
            self.galaxies[galaxy['type']] = Galaxy(galaxy)

    def validate_with_schema(self) -> None:
        """
        Validates the galaxies against the schema.

        Raises:
        - ImportError: If the jsonschema module is not installed.
        """
        if not HAS_JSONSCHEMA:
            raise ImportError('jsonschema is required: pip install jsonschema')
        schema = os.path.join(os.path.abspath(os.path.dirname(sys.modules['pymispgalaxies'].__file__)),  # type: ignore
                              'data', 'misp-galaxy', 'schema_galaxies.json')
        with open(schema, 'r') as f:
            loaded_schema = json.load(f)
        for g in self.galaxies.values():
            jsonschema.validate(g.galaxy, loaded_schema)

    def __getitem__(self, g_type: str) -> Galaxy:
        """
        Returns the galaxy with the specified type.

        Parameters:
        - g_type: The type of the galaxy.

        Returns:
        - The Galaxy instance with the specified type.

        Raises:
        - KeyError: If the galaxy with the specified type does not exist.
        """
        return self.galaxies[g_type]

    def __iter__(self) -> Iterator[str]:
        """
        Returns an iterator over the galaxy types.

        Returns:
        - An iterator over the galaxy types.
        """
        return iter(self.galaxies)

    def __len__(self) -> int:
        """
        Returns the number of galaxies in the collection.

        Returns:
        - The number of galaxies in the collection.
        """
        return len(self.galaxies)


class ClusterValueMeta():

    def __init__(self, m: Dict[str, str]):
        self.type = m.pop('type', None)
        self.complexity = m.pop('complexity', None)
        self.effectiveness = m.pop('effectiveness', None)
        self.country = m.pop('country', None)
        self.possible_issues = m.pop('possible_issues', None)
        self.colour = m.pop('colour', None)
        self.motive = m.pop('motive', None)
        self.impact = m.pop('impact', None)
        self.refs = m.pop('refs', None)
        self.synonyms = m.pop('synonyms', None)
        self.derivated_from = m.pop('derivated_from', None)
        self.status = m.pop('status', None)
        self.date = m.pop('date', None)
        self.encryption = m.pop('encryption', None)
        self.extensions = m.pop('extensions', None)
        self.ransomnotes = m.pop('ransomnotes', None)
        # NOTE: meta can have aditional properties. We only load the ones
        # defined on the schema
        self.additional_properties = m

    def to_json(self) -> str:
        return json.dumps(self, cls=EncodeClusters)

    def to_dict(self) -> Dict[str, str]:
        to_return = {}
        if self.type:
            to_return['type'] = self.type
        if self.complexity:
            to_return['complexity'] = self.complexity
        if self.effectiveness:
            to_return['effectiveness'] = self.effectiveness
        if self.country:
            to_return['country'] = self.country
        if self.possible_issues:
            to_return['possible_issues'] = self.possible_issues
        if self.colour:
            to_return['colour'] = self.colour
        if self.motive:
            to_return['motive'] = self.motive
        if self.impact:
            to_return['impact'] = self.impact
        if self.refs:
            to_return['refs'] = self.refs
        if self.synonyms:
            to_return['synonyms'] = self.synonyms
        if self.derivated_from:
            to_return['derivated_from'] = self.derivated_from
        if self.status:
            to_return['status'] = self.status
        if self.date:
            to_return['date'] = self.date
        if self.encryption:
            to_return['encryption'] = self.encryption
        if self.extensions:
            to_return['extensions'] = self.extensions
        if self.ransomnotes:
            to_return['ransomnotes'] = self.ransomnotes
        if self.additional_properties:
            to_return.update(self.additional_properties)
        return to_return


class ClusterValue():
    """
    Represents a cluster value.

    Attributes:
        uuid (str): The UUID of the cluster value.
        value (Any): The value of the cluster.
        description (str): The description of the cluster value.
        meta (ClusterValueMeta): The metadata associated with the cluster value.
        searchable (List[str]): A list of searchable terms for the cluster value.

    Methods:
        __init__(self, v: Dict[str, Any]): Initializes a ClusterValue object.
        __init_meta(self, m: Optional[Dict[str, str]]) -> Optional[ClusterValueMeta]: Initializes the metadata for the cluster value.
        to_json(self) -> str: Converts the ClusterValue object to a JSON string.
        to_dict(self) -> Dict[str, Any]: Converts the ClusterValue object to a dictionary.
    """

    def __init__(self, v: Dict[str, Any]):
        """
        Initializes a ClusterValue object.

        Args:
            v (Dict[str, Any]): A dictionary containing the cluster value information.

        Raises:
            PyMISPGalaxiesError: If the cluster value is invalid (no value).
        """
        if not v['value']:
            raise PyMISPGalaxiesError("Invalid cluster (no value): {}".format(v))
        self.uuid = v.get('uuid', None)
        self.value = v['value']
        self.description = v.get('description')
        self.meta = self.__init_meta(v.get('meta'))
        self.related = []
        try:
            # LATER convert related to a class?
            self.related = v['related']
        except KeyError:
            pass
        self.searchable = [self.value]
        if self.uuid:
            self.searchable.append(self.uuid)
        if self.meta and self.meta.synonyms:
            self.searchable += self.meta.synonyms
        self.searchable = list(set(self.searchable))

    def __init_meta(self, m: Optional[Dict[str, str]]) -> Optional[ClusterValueMeta]:
        """
        Initializes the metadata for the cluster value.

        Args:
            m (Optional[Dict[str, str]]): A dictionary containing the metadata for the cluster value.

        Returns:
            Optional[ClusterValueMeta]: The initialized ClusterValueMeta object or None if no metadata is provided.
        """
        if not m:
            return None
        return ClusterValueMeta(m)

    def to_json(self) -> str:
        """
        Converts the ClusterValue object to a JSON string.

        Returns:
            str: The JSON representation of the ClusterValue object.
        """
        return json.dumps(self, cls=EncodeClusters)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the ClusterValue object to a dictionary.

        Returns:
            Dict[str, Any]: The dictionary representation of the ClusterValue object.
        """
        to_return = {'value': self.value}
        if self.uuid:
            to_return['uuid'] = self.uuid
        if self.description:
            to_return['description'] = self.description
        if self.meta:
            to_return['meta'] = self.meta
        if self.related:
            to_return['related'] = self.related
        return to_return


class Cluster(Mapping):  # type: ignore
    """
    Represents a cluster in the PyMISPGalaxies library.

    Attributes:
        cluster (Dict[str, Any]): The dictionary containing the cluster data.
        cluster (str): The name of the existing cluster to load from the data folder.
        name (str): The name of the cluster.
        type (str): The type of the cluster.
        source (str): The source of the cluster.
        authors (str): The authors of the cluster.
        description (str): The description of the cluster.
        uuid (str): The UUID of the cluster.
        version (str): The version of the cluster.
        category (str): The category of the cluster.
        cluster_values (Dict[str, ClusterValue]): A dictionary containing the cluster values, where the keys are the values of the cluster and the values are instances of the ClusterValue class.
        duplicates (List[Tuple[str, str]]): A list of tuples representing duplicate values in the cluster, where each tuple contains the name of the cluster and the duplicate value.

    Methods:
        __init__(self, cluster: Dict[str, Any] | str, skip_duplicates: bool = False): Initializes a Cluster object from a dict or existing cluster file
        search(self, query: str, return_tags: bool = False) -> Union[List[ClusterValue], List[str]]: Searches for values in the cluster that match the given query.
        machinetags(self) -> List[str]: Returns a list of machine tags for the cluster.
        get_by_external_id(self, external_id: str) -> ClusterValue: Returns the cluster value with the specified external ID.
        save(self, name:str) -> None: Saves the cluster to a file <name>.json
        __str__(self) -> str: Returns a string representation of the cluster.
        __getitem__(self, name: str) -> ClusterValue: Returns the cluster value with the specified name.
        __len__(self) -> int: Returns the number of cluster values in the cluster.
        __iter__(self) -> Iterator[str]: Returns an iterator over the cluster values.
        to_json(self) -> str: Converts the Cluster object to a JSON string.
        to_dict(self) -> Dict[str, Any]: Converts the Cluster object to a dictionary.
    """

    def __init__(self, cluster: Union[Dict[str, Any], str], skip_duplicates: bool = False):
        """
        Initializes a Cluster object from an existing cluster.

        Args:
            cluster (str): The name of the existing cluster to load from the data folder.
            cluster (Dict[str, Any]): A dictionary containing the cluster data.
            skip_duplicates (bool, optional): Flag indicating whether to skip duplicate values. Defaults to False.
        """
        if isinstance(cluster, str):
            root_dir_clusters = os.path.join(os.path.abspath(os.path.dirname(sys.modules['pymispgalaxies'].__file__)), 'data', 'misp-galaxy', 'clusters')  # type: ignore [type-var, arg-type]
            cluster_file = os.path.join(root_dir_clusters, f"{cluster}.json")
            with open(cluster_file, 'r') as f:
                self.cluster = json.load(f)
        else:
            self.cluster = cluster
        self.name = self.cluster['name']
        self.type = self.cluster['type']
        self.source = self.cluster['source']
        self.authors = self.cluster['authors']
        self.description = self.cluster['description']
        self.uuid = self.cluster['uuid']
        self.version = self.cluster['version']
        self.category = self.cluster['category']
        self.cluster_values: Dict[str, Any] = {}
        self.duplicates: List[Tuple[str, str]] = []
        try:
            for value in self.cluster['values']:
                new_cluster_value = ClusterValue(value)
                self.append(new_cluster_value, skip_duplicates)
        except KeyError:
            pass

    @overload
    def search(self, query: str, return_tags: Literal[False] = False) -> List[ClusterValue]:
        ...

    @overload
    def search(self, query: str, return_tags: Literal[True]) -> List[str]:
        ...

    @overload
    def search(self, query: str, return_tags: bool) -> Union[List[ClusterValue], List[str]]:
        ...

    def search(self, query: str, return_tags: bool = False) -> Union[List[ClusterValue], List[str]]:
        """
        Searches for values in the cluster that match the given query.

        Args:
            query (str): The query to search for.
            return_tags (bool, optional): Flag indicating whether to return machine tags instead of cluster values. Defaults to False.

        Returns:
            Union[List[ClusterValue], List[str]]: A list of matching cluster values or machine tags.
        """
        matching = []
        for v in self.values():
            if [s for s in v.searchable if query.lower() in s.lower()]:
                if return_tags:
                    matching.append('misp-galaxy:{}="{}"'.format(self.type, v.value))
                else:
                    matching.append(v)
        return matching

    def machinetags(self) -> List[str]:
        """
        Returns a list of machine tags for the cluster.

        Returns:
            List[str]: A list of machine tags.
        """
        to_return = []
        for v in self.values():
            to_return.append('misp-galaxy:{}="{}"'.format(self.type, v.value))
        return to_return

    def get_by_external_id(self, external_id: str) -> ClusterValue:
        """
        Returns the cluster value with the specified external ID.

        Args:
            external_id (str): The external ID to search for.

        Returns:
            ClusterValue: The cluster value with the specified external ID.

        Raises:
            KeyError: If no value with the specified external ID is found.
        """
        for value in self.cluster_values.values():
            if value.meta and value.meta.additional_properties and value.meta.additional_properties.get('external_id') == external_id:
                return value
        raise KeyError('No value with external_id: {}'.format(external_id))

    def get_kill_chain_tactics(self) -> Dict[str, List[str]]:
        """
        Returns the sorted kill chain tactics associated with the cluster.

        Returns:
            List[str]: A list of kill chain tactics.
        """
        items = set()
        for v in self.cluster_values.values():
            if v.meta and v.meta.additional_properties and v.meta.additional_properties.get('kill_chain'):
                for item in v.meta.additional_properties.get('kill_chain'):
                    items.add(item)
        result: Dict[str, List[str]] = {}
        for item in items:
            key, value = item.split(':')
            if key not in result:
                result[key] = []
            result[key].append(value)

        for key in result.keys():
            result[key] = sorted(result[key])
        return result

    def append(self, cv: Union[Dict[str, Any], ClusterValue], skip_duplicates: bool = False) -> None:
        """
        Adds a cluster value to the cluster.
        """
        if isinstance(cv, dict):
            cv = ClusterValue(cv)
        if self.get(cv.value):
            if skip_duplicates:
                self.duplicates.append((self.name, cv.value))
            else:
                raise PyMISPGalaxiesError("Duplicate value ({}) in cluster: {}".format(cv.value, self.name))
        self.cluster_values[cv.value.lower()] = cv

    def save(self, name: str) -> None:
        """
        Saves the cluster to a file <name>.json

        Args:
            name (str): The name of the file to save the cluster to.
        """
        root_dir_clusters = os.path.join(os.path.abspath(os.path.dirname(sys.modules['pymispgalaxies'].__file__)), 'data', 'misp-galaxy', 'clusters')  # type: ignore [type-var, arg-type]
        cluster_file = os.path.join(root_dir_clusters, f"{name}.json")
        with open(cluster_file, 'w') as f:
            json.dump(self, f, cls=EncodeClusters, indent=2, sort_keys=True, ensure_ascii=False)
            f.write('\n')  # needed for the beauty and to be compliant with jq_all_the_things

    def __str__(self) -> str:
        """
        Returns a string representation of the cluster.

        Returns:
            str: A string representation of the cluster.
        """
        return '\n'.join(self.machinetags())

    def __getitem__(self, name: str) -> ClusterValue:
        """
        Returns the cluster value with the specified name.

        Args:
            name (str): The name of the cluster value.

        Returns:
            ClusterValue: The cluster value with the specified name.
        """
        return self.cluster_values[name.lower()]

    def __len__(self) -> int:
        """
        Returns the number of cluster values in the cluster.

        Returns:
            int: The number of cluster values.
        """
        return len(self.cluster_values)

    def __iter__(self) -> Iterator[str]:
        """
        Returns an iterator over the cluster values.

        Returns:
            Iterator[str]: An iterator over the cluster values.
        """
        return iter(self.cluster_values)

    def to_json(self) -> str:
        """
        Converts the Cluster object to a JSON string.

        Returns:
            str: The JSON representation of the Cluster object.
        """
        return json.dumps(self, cls=EncodeClusters)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Cluster object to a dictionary.

        Returns:
            Dict[str, Any]: The dictionary representation of the Cluster object.
        """
        to_return = {'name': self.name, 'type': self.type, 'source': self.source,
                     'authors': self.authors, 'description': self.description,
                     'uuid': self.uuid, 'version': self.version, 'category': self.category,
                     'values': []}
        to_return['values'] = [v for v in self.values()]
        return to_return


class Clusters(Mapping):  # type: ignore

    def __init__(self, clusters: List[Dict[str, str]] = [], skip_duplicates: bool = False):
        """
        Allows to interact with a group of clusters.

        Args:
            clusters (List[Dict[str, str]], optional): A list of dictionaries representing clusters. If left empty, load the clusters from the data folder.
            skip_duplicates (bool, optional): Flag indicating whether to skip duplicate clusters. Defaults to False.
        """
        if not clusters:
            clusters = []
            self.root_dir_clusters = os.path.join(os.path.abspath(os.path.dirname(sys.modules['pymispgalaxies'].__file__)),  # type: ignore
                                                  'data', 'misp-galaxy', 'clusters')
            for cluster_file in glob(os.path.join(self.root_dir_clusters, '*.json')):
                with open(cluster_file, 'r') as f:
                    clusters.append(json.load(f))
        self.clusters = {}
        for cluster in clusters:
            self.clusters[cluster['type']] = Cluster(cluster, skip_duplicates=skip_duplicates)

    def validate_with_schema(self) -> None:
        """
        Validates the clusters against the schema.

        Raises:
            ImportError: If jsonschema is not installed.
        """
        if not HAS_JSONSCHEMA:
            raise ImportError('jsonschema is required: pip install jsonschema')
        schema = os.path.join(os.path.abspath(os.path.dirname(sys.modules['pymispgalaxies'].__file__)),  # type: ignore
                              'data', 'misp-galaxy', 'schema_clusters.json')
        with open(schema, 'r') as f:
            loaded_schema = json.load(f)
        for c in self.values():
            jsonschema.validate(c.cluster, loaded_schema)

    def all_machinetags(self) -> List[str]:
        """
        Returns a list of all machinetags in the clusters.

        Returns:
            List[str]: A list of machinetags.
        """
        return [cluster.machinetags() for cluster in self.values()]

    def revert_machinetag(self, machinetag: str) -> Tuple[Cluster, ClusterValue]:
        """
        Reverts a machinetag to its original cluster and value.

        Args:
            machinetag (str): The machinetag to revert.

        Returns:
            Tuple[Cluster, ClusterValue]: A tuple containing the original cluster and value.

        Raises:
            UnableToRevertMachinetag: If the machinetag could not be found.
        """
        try:
            _, cluster_type, cluster_value = re.findall('^([^:]*):([^=]*)="([^"]*)"$', machinetag)[0]
            cluster: Cluster = self[cluster_type]
            value: ClusterValue = cluster[cluster_value]
            return cluster, value
        except Exception:
            raise UnableToRevertMachinetag('The machinetag {} could not be found.'.format(machinetag))

    def search(self, query: str, return_tags: bool = False) -> List[Tuple[Cluster, str]]:
        """
        Searches for clusters and values matching the given query.

        Args:
            query (str): The query to search for.
            return_tags (bool, optional): Flag indicating whether to return the matching tags. Defaults to False.

        Returns:
            List[Tuple[Cluster, str]]: A list of tuples containing the matching cluster and value.

        """
        to_return = []
        for cluster in self.values():
            values = cluster.search(query, return_tags)
            if not values:
                continue
            to_return.append((cluster, values))
        return to_return

    def __getitem__(self, name: str) -> Cluster:
        """
        Returns the cluster with the specified name.

        Args:
            name (str): The name of the cluster.

        Returns:
            Cluster: The cluster object.

        Raises:
            KeyError: If the cluster with the specified name does not exist.
        """
        return self.clusters[name]

    def __iter__(self) -> Iterator[str]:
        """
        Returns an iterator over the cluster names.

        Returns:
            Iterator[str]: An iterator over the cluster names.
        """
        return iter(self.clusters)

    def __len__(self) -> int:
        """
        Returns the number of clusters.

        Returns:
            int: The number of clusters.
        """
        return len(self.clusters)

    def __str__(self) -> str:
        """
        Returns a string representation of the Clusters object.

        Returns:
            str: A string representation of the Clusters object.
        """
        to_print = ''
        for cluster in self.values():
            to_print += '{}\n\n'.format(cluster)
        return to_print
