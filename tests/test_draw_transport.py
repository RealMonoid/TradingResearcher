"""Canonical byte transport must preserve complete numerical/draw results."""
import hashlib
import unittest

from bootstrap_support import report
from trading_researcher.codec import canonical
from trading_researcher.stationary_bootstrap import calculate,randomness


class DrawTransportTests(unittest.TestCase):
    def test_complete_draw_hashes_equal_dictionary_transport(self):
        rows=[];lines=[]
        result=calculate(report(times=4,rare=True),
            {'base_length':1,'primary_count':2,'randomness':randomness(913)},
            {'max_seconds':60,'max_segments':2000000},on_draw=rows.append,on_draw_bytes=lines.append)
        self.assertEqual(len(rows),19999*2)
        self.assertEqual(lines,[canonical(row).encode() for row in rows])
        for case in result['cases']:
            expected=hashlib.sha256(b''.join(raw+b'\n' for raw,row in zip(lines,rows) if row['length']==case['length'])).hexdigest()
            self.assertEqual(case['replicate_sha256'],expected)
        self.assertFalse(result['scientific_readiness'])


if __name__=='__main__':unittest.main()
