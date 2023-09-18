import unittest
import hw1_log_parser as lp

class TestLogParser(unittest.TestCase):
    
    def __init__(self, lp):
        self.lp = lp

    def test_str_date(self):
        self.assertEqual(lp.str_date('20230119'), '20230119')

    def test_median(self):
        self.assertEqual(lp.median([2, 3, 5, 7, 11, 13]), 6)
        self.assertEqual(lp.median([2, 3, 5, 7, 11]), 5)
    
    def test_utd(self):
        loglist = [['url_1', 0.000319],
                   ['url_2', 0.1363],
                   ['url_1', 1.380001]]
                    
        utd = {
             'url_1': [0.000319, 1.380001],
             'url_2': [0.1363]
             }
        self.assertEqual(lp.url_timepoints_dict(loglist), utd)
    
    def test_sorted_reqs(self):
        url_timesum = {
             'url_0': [0.000076],
             'url_1': [1.380329],
             'url_2': [0.1363]
             }
        
        sorted_dict = {
            'url_1': 1.380329,
            'url_2': 0.1363
        }
        report_size = 2
        self.assertEqual(lp.sorted_reqs(url_timesum, report_size), sorted_dict)
    
    def test_all_reqs_timesum(self):
        utd = {
             'url_1': [1,380329],
             'url_2': [0.1363]
             }
        
        utd_timesum = 1.516629

        self.assertEqual(lp.all_reqs_timesum(utd), utd_timesum)

if __name__ == "__main__":
    unittest.main(lp)

  


