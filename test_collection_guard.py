from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import collect_confirmation as cc


class CollectionGuardTests(unittest.TestCase):
    def test_judge_only_retains_budget_wrapper_and_skips_collection(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(cc.confirmation, "ROOT", Path(tmp)), patch.object(cc.confirmation, "verify"), patch.object(cc, "key_state", return_value={"limit_remaining":20}):
            arguments = []
            def original_main(argv):
                arguments.append(argv)
                return 0
            def execute(name, budget):
                self.assertEqual(budget, 35)
                self.assertEqual(cc.confirmation.sb.main(["run", "--workers", "16"]), 0)
                return cc.confirmation.sb.main(["judge", "--workers", "16", "--name", name])
            with patch.object(cc.confirmation.sb, "chat"), patch.object(cc.confirmation.sb, "main", original_main), patch.object(cc.confirmation, "execute", execute):
                self.assertEqual(cc.collect("example", judge_only=True), 0)
            self.assertEqual(arguments, [["judge", "--workers", "64", "--name", "example"]])

    def test_exhausted_key_stops_before_execute(self):
        with patch.object(cc.confirmation, "verify"), patch.object(cc, "key_state", return_value={"usage": 20, "limit":20, "limit_remaining":0}), patch.object(cc.confirmation, "execute") as execute:
            with self.assertRaisesRegex(ValueError, "exhausted"):
                cc.collect("example")
            execute.assert_not_called()

    def test_only_workers_change_and_rejection_stops_queue(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(cc.confirmation, "ROOT", Path(tmp)), patch.object(cc.confirmation, "verify"), patch.object(cc, "key_state", return_value={"usage":1,"limit":50,"limit_remaining":49}):
            sent, arguments, results = [], [], []
            def chat(*args):
                sent.append(args)
                return {"error":"HTTP 403: Forbidden"}
            def original_main(argv):
                arguments.append(argv)
                results.append(cc.confirmation.sb.chat({}, 1))
                results.append(cc.confirmation.sb.chat({}, 1))
                return 1
            def execute(name, budget):
                return cc.confirmation.sb.main(["run","--name",name,"--workers","16","--samples","5"])
            with patch.object(cc.confirmation.sb,"chat",chat), patch.object(cc.confirmation.sb,"main",original_main), patch.object(cc.confirmation,"execute",execute):
                self.assertEqual(cc.collect("example",35,64),1)
            self.assertEqual(arguments,[["run","--name","example","--workers","64","--samples","5"]])
            self.assertEqual(len(sent),1)
            self.assertTrue(results[1]["not_sent"])


if __name__ == '__main__':
    unittest.main()
