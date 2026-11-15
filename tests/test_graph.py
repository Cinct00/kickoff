"""Unit tests for codemap's graph algorithms. Run: python3 -m unittest discover -s tests"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugins" / "codemap" / "scripts"))

from codemap_core.graph import pagerank, strongly_connected  # noqa: E402


class PageRankTest(unittest.TestCase):
    def test_empty_graph(self):
        self.assertEqual(pagerank([], {}), {})

    def test_scores_sum_to_one_and_hub_ranks_highest(self):
        nodes = ["a", "b", "c", "hub"]
        edges = {"a": {"hub": 1}, "b": {"hub": 1}, "c": {"hub": 1}, "hub": {"a": 1}}
        rank = pagerank(nodes, edges)
        self.assertAlmostEqual(sum(rank.values()), 1.0, places=6)
        self.assertEqual(max(rank, key=rank.get), "hub")

    def test_dangling_nodes_keep_total_mass(self):
        nodes = ["a", "b", "sink"]
        rank = pagerank(nodes, {"a": {"sink": 1}, "b": {"sink": 1}})  # sink has no out-edges
        self.assertAlmostEqual(sum(rank.values()), 1.0, places=6)
        self.assertGreater(rank["sink"], rank["a"])

    def test_edge_weights_matter(self):
        nodes = ["src", "heavy", "light"]
        rank = pagerank(nodes, {"src": {"heavy": 9, "light": 1}})
        self.assertGreater(rank["heavy"], rank["light"])

    def test_personalization_biases_towards_seed(self):
        nodes = ["a", "b", "c", "d"]
        edges = {"a": {"b": 1}, "b": {"c": 1}, "c": {"d": 1}, "d": {"a": 1}}
        plain = pagerank(nodes, edges)
        seeded = pagerank(nodes, edges, personalization={"c": 1.0})
        self.assertAlmostEqual(plain["a"], plain["c"], places=4)  # a ring is uniform
        self.assertGreater(seeded["c"], seeded["a"])
        self.assertGreater(seeded["d"], seeded["b"])  # mass flows downstream of the seed

    def test_edges_to_unknown_nodes_are_ignored(self):
        rank = pagerank(["a", "b"], {"a": {"b": 1, "ghost": 1}})
        self.assertEqual(set(rank), {"a", "b"})


class StronglyConnectedTest(unittest.TestCase):
    def test_finds_cycles_largest_first(self):
        nodes = ["a", "b", "c", "d", "e", "x", "y"]
        edges = {"a": {"b": 1}, "b": {"c": 1}, "c": {"a": 1},   # 3-cycle
                 "d": {"e": 1}, "e": {"d": 1},                   # 2-cycle
                 "x": {"y": 1}}                                   # acyclic
        comps = strongly_connected(nodes, edges)
        self.assertEqual([sorted(c) for c in comps], [["a", "b", "c"], ["d", "e"]])

    def test_acyclic_graph_and_self_loop_have_no_components(self):
        self.assertEqual(strongly_connected(["a", "b", "c"], {"a": {"b": 1}, "b": {"c": 1}}), [])
        self.assertEqual(strongly_connected(["a"], {"a": {"a": 1}}), [])  # single nodes are not reported

    def test_long_chain_does_not_recurse(self):
        n = 5000  # deeper than Python's default recursion limit
        nodes = [str(i) for i in range(n)]
        edges = {str(i): {str(i + 1): 1} for i in range(n - 1)}
        edges[str(n - 1)] = {"0": 1}
        comps = strongly_connected(nodes, edges)
        self.assertEqual(len(comps), 1)
        self.assertEqual(len(comps[0]), n)


if __name__ == "__main__":
    unittest.main()
