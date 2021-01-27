import difflib
import os
import pickle
import sportsbetting
import sys
from sportsbetting.user_functions import best_match_under_conditions

def are_identical_files(filename1, filename2):
    lines1 = []
    lines2 = []
    with open(filename1) as f:
        for line in f:
            lines1.append(line.strip())
    with open(filename2) as f:
        for line in f:
            lines2.append(line.strip())
    diffs = list(difflib.unified_diff(lines1, lines2))
    if not diffs:
        return True
    
    print(diffs)
    return False
    

def test_under_condition():
    PATH_DATA_TEST = os.path.dirname(sportsbetting.__file__) + "/resources/data_test.pickle"
    sportsbetting.ODDS = pickle.load(open(PATH_DATA_TEST, "rb"))
    original_stdout = sys.stdout
    reached = os.path.dirname(sportsbetting.__file__) + "/tests/result_under_condition_1_reached.txt"
    expected = os.path.dirname(sportsbetting.__file__) + "/tests/result_under_condition_1_expected.txt"
    with open(reached, "w") as f:
        sys.stdout = f
        best_match_under_conditions("parionssport", 1.7, 10)
    sys.stdout = original_stdout
    assert(are_identical_files(expected, reached))
        
    reached = os.path.dirname(sportsbetting.__file__) + "/tests/result_under_condition_2_reached.txt"
    expected = os.path.dirname(sportsbetting.__file__) + "/tests/result_under_condition_2_expected.txt"
    with open(reached, "w") as f:
        sys.stdout = f
        best_match_under_conditions("parionssport", 1.7, 10, date_min="23/11/2020")
    sys.stdout = original_stdout
    assert(are_identical_files(expected, reached))
    
    reached = os.path.dirname(sportsbetting.__file__) + "/tests/result_under_condition_3_reached.txt"
    expected = os.path.dirname(sportsbetting.__file__) + "/tests/result_under_condition_3_expected.txt"
    with open(reached, "w") as f:
        sys.stdout = f
        best_match_under_conditions("parionssport", 1.7, 10, date_min="23/11/2020", date_max="29/11/2020")
    sys.stdout = original_stdout
    assert(are_identical_files(expected, reached))
    
    

