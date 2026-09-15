import unittest

from .. import mutation_claimed_rows
from .. import vendor_stock_content_data
from .bases import WoWTestBase


class TestClaimedRowsAgainstRealGeneration(WoWTestBase):
    """Sec4's own Testing requirement: a row already present in a Pipeline
    A family's compiled output for a REAL generation must never appear in
    a Pipeline B category's candidate pool for that same generation. Forces
    vendor_stock_weight high (WoWTestBase defaults it to 0 for speed) so at
    least some real Vendor Inventories locations are actually placed."""
    options = {"vendor_stock_weight": 100}

    def test_placed_vendor_locations_are_excluded_from_a_synthetic_category(self):
        claimed = mutation_claimed_rows.claimed_rows(self.world)
        self.assertTrue(claimed, "expected at least one real claimed row with vendor_stock_weight=100")

        # Every (npc_entry, item_slot) pair Pipeline A's real family TRIGGERS
        # table knows about -- the full static superset, exactly the shape
        # a Pipeline B economy category's own candidate_rows() would use.
        all_vendor_candidates = {
            ("npc_vendor", (trigger["npc_entry"], trigger["item_slot"]))
            for trigger in vendor_stock_content_data.TRIGGERS.values()
        }
        excluded = all_vendor_candidates - claimed
        claimed_vendor_rows = {row for row in claimed if row[0] == "npc_vendor"}

        self.assertTrue(claimed_vendor_rows, "expected at least one real claimed npc_vendor row")
        # Every claimed npc_vendor row must be absent from the post-exclusion set.
        for row in claimed_vendor_rows:
            self.assertNotIn(row, excluded)
        # And at least one candidate must survive exclusion (not every real
        # vendor row in the whole game got placed by this one seed).
        self.assertTrue(excluded)


if __name__ == "__main__":
    unittest.main()
