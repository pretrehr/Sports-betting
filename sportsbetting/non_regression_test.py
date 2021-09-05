import difflib
import os
import sportsbetting as sb
import sys
from sportsbetting.auxiliary_functions import load_odds
from sportsbetting.user_functions import best_match_under_conditions, best_match_under_conditions2

def are_identical_files(filename1, filename2):
    lines1 = []
    lines2 = []
    with open(filename1, encoding="utf-8") as f:
        for line in f:
            lines1.append(line.strip())
    with open(filename2, encoding="utf-8") as f:
        for line in f:
            lines2.append(line.strip())
    diffs = list(difflib.unified_diff(lines1, lines2))
    if not diffs:
        return True
    print(diffs)
    return False
    

def test_under_condition(update_references=False):
    PATH_DATA_TEST = os.path.dirname(sb.__file__) + "/resources/data_test.json"
    sb.ODDS = load_odds(PATH_DATA_TEST)
    original_stdout = sys.stdout
    reached = os.path.dirname(sb.__file__) + "/tests/result_under_condition_1_reached.txt"
    expected = os.path.dirname(sb.__file__) + "/tests/result_under_condition_1_expected.txt"
    with open(expected if update_references else reached, "w", encoding="utf-8") as f:
        sys.stdout = f
        best_match_under_conditions("parionssport", 1.7, 10)
    sys.stdout = original_stdout
    assert(update_references or are_identical_files(expected, reached))
        
    reached = os.path.dirname(sb.__file__) + "/tests/result_under_condition_2_reached.txt"
    expected = os.path.dirname(sb.__file__) + "/tests/result_under_condition_2_expected.txt"
    with open(expected if update_references else reached, "w", encoding="utf-8") as f:
        sys.stdout = f
        best_match_under_conditions("parionssport", 1.7, 10, date_min="23/11/2020")
    sys.stdout = original_stdout
    assert(update_references or are_identical_files(expected, reached))
    
    reached = os.path.dirname(sb.__file__) + "/tests/result_under_condition_3_reached.txt"
    expected = os.path.dirname(sb.__file__) + "/tests/result_under_condition_3_expected.txt"
    with open(expected if update_references else reached, "w", encoding="utf-8") as f:
        sys.stdout = f
        best_match_under_conditions("parionssport", 1.7, 10, date_min="23/11/2020", date_max="29/11/2020")
    sys.stdout = original_stdout
    assert(update_references or are_identical_files(expected, reached))

def test_under_condition_same_site(update_references=False):
    PATH_DATA_TEST = os.path.dirname(sb.__file__) + "/resources/data_test.json"
    sb.ODDS = load_odds(PATH_DATA_TEST)
    original_stdout = sys.stdout
    reached = os.path.dirname(sb.__file__) + "/tests/result_under_condition_same_site_1_reached.txt"
    expected = os.path.dirname(sb.__file__) + "/tests/result_under_condition_same_site_1_expected.txt"
    with open(expected if update_references else reached, "w", encoding="utf-8") as f:
        sys.stdout = f
        best_match_under_conditions2("pmu", 1.4, 10)
    sys.stdout = original_stdout
    assert(update_references or are_identical_files(expected, reached))
    
    original_stdout = sys.stdout
    reached = os.path.dirname(sb.__file__) + "/tests/result_under_condition_same_site_2_reached.txt"
    expected = os.path.dirname(sb.__file__) + "/tests/result_under_condition_same_site_2_expected.txt"
    with open(expected if update_references else reached, "w", encoding="utf-8") as f:
        sys.stdout = f
        best_match_under_conditions2("pmu", 2.6, 10)
    sys.stdout = original_stdout
    assert(update_references or are_identical_files(expected, reached))
    
    original_stdout = sys.stdout
    reached = os.path.dirname(sb.__file__) + "/tests/result_under_condition_same_site_3_reached.txt"
    expected = os.path.dirname(sb.__file__) + "/tests/result_under_condition_same_site_3_expected.txt"
    with open(expected if update_references else reached, "w", encoding="utf-8") as f:
        sys.stdout = f
        best_match_under_conditions2("pmu", 2.6, 10, date_min="24/11/2020")
    sys.stdout = original_stdout
    assert(update_references or are_identical_files(expected, reached))
    
    original_stdout = sys.stdout
    reached = os.path.dirname(sb.__file__) + "/tests/result_under_condition_same_site_4_reached.txt"
    expected = os.path.dirname(sb.__file__) + "/tests/result_under_condition_same_site_4_expected.txt"
    with open(expected if update_references else reached, "w", encoding="utf-8") as f:
        sys.stdout = f
        best_match_under_conditions2("pmu", 2.6, 10, date_min="24/11/2020", date_max="29/11/2020")
    sys.stdout = original_stdout
    assert(update_references or are_identical_files(expected, reached))
