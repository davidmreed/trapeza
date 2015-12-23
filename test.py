# -*- coding: utf-8 -*-
#
#  trapeza/test.py
#  
#  Copyright 2013-2014 David Reed <david@ktema.org>
#  This file is available under the terms of the MIT License.

import StringIO
import trapeza
import trapeza.match
import unittest


class TestTrapeza(unittest.TestCase):

    def test_record(self):
        a = trapeza.Record({u"Name": u"Test 1", u"ID": 1, u"Data": u"Test 1 Data"}, primary_key=u"ID")
        b = trapeza.Record({u"Name": u"Test 2", u"ID": 2, u"Data": u"Test 2 Data"}, primary_key=u"ID")
        
        self.assertEqual(a.record_id(), 1)
        self.assertEqual(a.values[u"Name"], u"Test 1")
        self.assertNotEqual(a, b)
        
        b.values[u"ID"] = 1
        
        self.assertEqual(a, b)
        
        c = trapeza.Record(a.values)
        
        self.assertNotEqual(a, c)
        
        a.primary_key = None
        
        self.assertEqual(a, c)
        
        self.assertNotEqual(a, 1)
        
    def test_source(self):
        a = trapeza.Source([u"Name", u"ID", u"Email"])
        
        b = trapeza.Record({u"Name": u"Test 1", u"ID": 1, u"Email": u"test1@test1.com"})
        
        a.add_record(b)
        self.assertEqual(a.records(), [b])
        
        a.set_primary_key(u"ID")
        self.assertEqual(a.get_record_with_id(1), b)
        
        a.add_column(u"Test")
        self.assertEqual(a.headers(), [u"Name", u"ID", u"Email", u"Test"])
        
        a.drop_column(u"Test")
        self.assertEqual(a.headers(), [u"Name", u"ID", u"Email"])
        
        self.assertTrue(a.contains_record(b))
        a.set_primary_key(None)
        self.assertTrue(a.contains_record(b))
        
        a.del_record(b)
        self.assertEqual(len(a.records()), 0)
        a.add_record(b)
        self.assertEqual(len(a.records()), 1)
        a.set_primary_key(u"ID")
        a.del_record_with_id(1)
        self.assertEqual(len(a.records()), 0)
        a.add_record(b)
        self.assertEqual(len(a.records()), 1)
        
        c = trapeza.Record({u"Name": u"Test 2", u"ID": 2, u"Email": u"test2@test2.com"})
        d = trapeza.Record({u"Name": u"Test 3", u"ID": 3, u"Email": u"test3@test3.com"})
        a.add_record(d)
        a.add_record(c)
        
        a.filter_records(lambda rec: rec.values[u"ID"] == 2)
        self.assertEqual(a.records(), [c])
        
        a.add_record(b)
        a.add_record(d)
        
        e = trapeza.Record({u"Name": u"Test 3", u"ID": 4, u"Email": u"test3@test3.com"})
        a.add_record(e, 0)
        self.assertEqual(a.records()[0], e)
        
        a.sort_records([(u"Name", True, "string"), (u"ID", True, "number")])
        self.assertEqual(a.records(), [b, c, d, e])
        
        self.assertTrue(a.contains_record(e))
        a.set_primary_key(None)
        self.assertTrue(a.contains_record(e))
        a.del_record(e)
        self.assertFalse(a.contains_record(e))
        
    def test_get_format(self):
        self.assertEqual(trapeza.get_format("test.tsv"), "tsv")
        self.assertEqual(trapeza.get_format("test"), "csv")
        self.assertEqual(trapeza.get_format("test", "chr"), "chr")
        
    def test_unify_sources(self):
        a = trapeza.Source([u"Name", u"ID", u"Email"])
        b = trapeza.Source([u"Name", u"ID", u"Email"])
        
        self.assertTrue(trapeza.sources_consistent([a, b]))
        b.drop_column(u"Email")
        self.assertFalse(trapeza.sources_consistent([a, b]))
        
        trapeza.unify_sources([a, b])
        self.assertTrue(trapeza.sources_consistent([a, b]))
        
    def test_load_save(self):
        test_data = u"Name,Donations,ID\nTim,500,1\nMary,125.3,2\nSam Smith,12000,3\nKen,250,4\nΕὐθύφρων,150,5"\
            .encode("utf-8")
        infile = StringIO.StringIO(test_data)

        a = trapeza.load_source(infile, "csv", encoding="utf-8")
        self.assertEqual(len(a.records()), 5)
        a.set_primary_key(u"ID")
    
        self.assertEqual(a.get_record_with_id(u"5").values[u"Name"], u"Εὐθύφρων")
        
        of = StringIO.StringIO()
        trapeza.write_source(a, of, "csv", encoding="utf-8")
        
        b = trapeza.load_source(StringIO.StringIO(of.getvalue()), "csv", encoding="utf-8")
        self.assertEqual(len(b.records()), 5)
        b.set_primary_key(u"ID")
        self.assertEqual(b.get_record_with_id(u"5").values[u"Name"], u"Εὐθύφρων")


class TestMatch(unittest.TestCase):
    def test_mapping(self):
        ra = trapeza.Record({u"Name": u"Tim"})
        rb = trapeza.Record({u"Name": u"Timothy"})
        rc = trapeza.Record({u"Name": u"Dave"})
        
        a = trapeza.match.Mapping(u"Name", u"Name", trapeza.match.COMPARE_EXACT, 1)
        
        self.assertEqual(a.compare_records(ra, rb), 0)
        self.assertEqual(a.compare_records(ra, ra), 1)
        
        a.compare = trapeza.match.COMPARE_PREFIX
        self.assertEqual(a.compare_records(ra, rb), 1)
        self.assertEqual(a.compare_records(ra, rc), 0)
        
        a.compare = trapeza.match.COMPARE_FUZZY
        self.assertGreater(a.compare_records(ra, rb), 0)
        # Nilsimsa hashing doesn't work as expected for short strings - it works on long strings
        # FIXME: use a better locality-sensitive hash.
        # self.assertGreater(a.compare_records(ra, rb), a.compare_records(ra, rc))
        
    def test_profile(self):
        ra = trapeza.Record({u"Name": u"Tim", u"Address": u"130 Main St."})
        rb = trapeza.Record({u"Name": u"Timothy", u"Address": u"2345 Sycamore Ln."})
        rc = trapeza.Record({u"Name": u"Dave", u"Address": u"130 Main"})
        
        a = trapeza.match.Mapping(u"Name", u"Name", trapeza.match.COMPARE_EXACT, 1)
        b = trapeza.match.Mapping(u"Address", u"Address", trapeza.match.COMPARE_PREFIX, 1)
        # FIXME: Add fuzzy matching when our hashing issues are fixed.
        
        p = trapeza.match.Profile(mappings=[a, b])
        
        self.assertEqual(p.compare_records(ra, rb), 0)
        self.assertEqual(p.compare_records(ra, rc), 1)
        
        sa = trapeza.Source(ra.values.keys())
        sa.add_record(ra)
        sa.add_record(rb)
        
        sb = trapeza.Source(ra.values.keys())
        sb.add_record(rc)
        
        r = p.compare_sources(sa, sb, 1)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0].incoming, rc)
        self.assertEqual(r[0].master, ra)
        self.assertEqual(r[0].score, 1)
        
    def test_process(self):
        ra = trapeza.Record({u"Name": u"Tim", u"Address": u"130 Main St."})
        rb = trapeza.Record({u"Name": u"Timothy", u"Address": u"2345 Sycamore Ln."})
        rc = trapeza.Record({u"Name": u"Dave", u"Address": u"130 Main"})
        
        a = trapeza.match.Mapping(u"Name", u"Name", trapeza.match.COMPARE_EXACT, 1)
        b = trapeza.match.Mapping(u"Name", u"Name", trapeza.match.COMPARE_PREFIX, 1)
        c = trapeza.match.Mapping(u"Address", u"Address", trapeza.match.COMPARE_PREFIX, 1)
        d = trapeza.match.Mapping(u"Address", u"Address", trapeza.match.COMPARE_EXACT, 1)

        p = trapeza.match.Profile(mappings=[a, b, c, d])
                
        sa = trapeza.Source(ra.values.keys())
        sa.add_record(ra)
        sa.add_record(rb)
        sa.set_primary_key(u"Name")
        
        sb = trapeza.Source(ra.values.keys())
        sb.add_record(rc)
        sb.set_primary_key(u"Name")
        
        pc = trapeza.match.ProcessedSource(sa, True, p)
        pc.process()
        
        # FIXME: This test fails on certain profiles due to differences
        # in how fuzzy matching works on a processed versus unprocessed source.
        # Processed hashes are coalesced by similarity to a base string.
        r = p.compare_sources(pc, sb, 0)
        r_prime = p.compare_sources(sa, sb, 0)
        self.assertEqual(r, r_prime)


if __name__ == '__main__':
    unittest.main()
