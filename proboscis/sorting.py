# Copyright (c) 2011 Rackspace
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from collections import deque

class TestNode:
    """Representation of a TestEntry used in sorting."""
    def __init__(self, case):
        self.case = case
        self.dependencies = []
        self.dependents = []

    def add_dependency(self, node):
        """Adds a bidirectional link between this node and a dependency.

        This also informs the dependency TestEntry of its dependent.  It is
        intuitive to specify dependencies when writing tests, so we have
        to wait until this phase to determine the dependents of the TestEntry.

        """
        # TODO: Could this be sped up by using a set?
        if node in self.dependencies:
            return
        self.dependencies.append(node)
        node.dependents.append(self)
        node.case.dependents.append(self.case)

    @property
    def has_no_dependencies(self):
        return len(self.dependencies) == 0

    def pop_dependent(self):
        """Removes and returns a dependent from this nodes dependent list.

        This act of destruction is one reason why this second representation
        of a TestEntry is necessary.

        """
        dependent = self.dependents.pop()
        dependent.dependencies.remove(self)
        return dependent


class TestGraph:
    """Used to sort the tests in a registry in the correct order.

    As it sorts, it also adds dependent information to the TestEntries, which
    means calling it twice messes stuff up.

    """

    def __init__(self, groups, entries, cases):
        self.nodes = []
        self.entries = entries
        self.groups = groups
        for case in cases:
            self.nodes.append(TestNode(case))
        for node in self.nodes:
            for dependency_group in node.case.entry.info.depends_on_groups:
                d_group_nodes = self.nodes_for_group(dependency_group)
                for dependency_group_node in d_group_nodes:
                    node.add_dependency(dependency_group_node)
            for dependency in node.case.entry.info.depends_on:
                d_nodes = self.nodes_for_class_or_function(dependency)
                for dependency_node in d_nodes:
                    node.add_dependency(dependency_node)

#    def node_for_case(self, case):
#        """Finds the node attached to the given case."""
#        for node in self.nodes:
#            if node.case is case:
#                return node
#        raise RuntimeError("Could not find node for case " + str(case))

    def nodes_for_class_or_function(self, test_home):
        """Returns nodes attached to the given class."""
        return (n for n in self.nodes if n.case.entry.home is test_home)

    def nodes_for_group(self, group_name):
        """Returns nodes attached to the given group."""
        group = self.groups[group_name]
        entries = group.entries
        return [node for node in self.nodes if node.case.entry in entries]

    def sort(self):
        """Returns a sorted list of entries.

        Dismantles this graph's list of nodes and adds dependent information
        to the list of TestEntries (iow don't call this twice).

        """
        independent_nodes = deque((n for n in self.nodes
                                   if n.has_no_dependencies))
        ordered_nodes = []  # The new list
        while independent_nodes:
            i_node = independent_nodes.popleft()
            ordered_nodes.append(i_node)
            while i_node.dependents:
                d_node = i_node.pop_dependent()
                if d_node.has_no_dependencies:
                    independent_nodes.appendleft(d_node)
        # Search for a cycle
        for node in self.nodes:
            if not node.has_no_dependencies:
                raise RuntimeError("Cycle found on node " + str(node.case))
        return list((n.case for n in ordered_nodes))
