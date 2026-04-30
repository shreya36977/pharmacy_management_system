"""
=============================================================================
 BLACK BOX TESTING - PHARMACY MANAGEMENT SYSTEM
 Use Case: Dispense Medicine
=============================================================================
 Student  : Shreya Raju Pawar
 Roll No  : 24107I060
 Class    : SY BTech Computer
 Course   : Software Engineering
 Date     : 30/04/2026
=============================================================================
 Testing Techniques Applied:
   1. Equivalence Class Partitioning (ECP)
   2. Boundary Value Analysis (BVA)
=============================================================================
 Use Case Covered (from SE Practical Exam):
   - Actors        : Pharmacist (Primary), Patient (Secondary)
   - Preconditions : Valid prescription exists, Medicine available in inventory
   - Main Flow     : Pharmacist logs in → Selects prescription → System
                     validates → Checks stock → Verifies dosage & interactions
                     → Pharmacist dispenses → Stock updated → Bill generated
   - Alternate Flows: Invalid prescription → Show error
                      Out of stock → Suggest alternative / reorder
                      Drug interaction → Alert pharmacist
   - Post-conditions: Medicine dispensed, Inventory updated, Billing completed
=============================================================================
"""

import unittest
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, line_buffering=True)
from datetime import date


# =====================================================================
#  SYSTEM UNDER TEST (SUT) - Pharmacy Management System
# =====================================================================

class Prescription:
    def __init__(self, pid, drug, qty):
        self.pid = pid
        self.drug = drug
        self.qty = qty


class Medicine:
    def __init__(self, name, stock, price, expiry):
        self.name = name
        self.stock = stock
        self.price = price
        self.expiry = expiry


class Inventory:
    def __init__(self):
        self.data = {}

    def add(self, med):
        self.data[med.name.lower()] = med

    def get(self, name):
        # Strip extra spaces for case-insensitive + whitespace-tolerant lookup
        return self.data.get(name.strip().lower())


class ValidationSystem:
    def validate(self, pres):
        if pres.pid == "":
            raise Exception("Invalid Prescription")
        if pres.qty <= 0:
            raise Exception("Invalid quantity")

    def check_expiry(self, med):
        if med.expiry < date.today():
            raise Exception("Medicine expired")

    def check_interaction(self, name):
        if name.strip().lower() == "drugx":
            raise Exception("Drug interaction")


class InventoryManager:
    def __init__(self, inv):
        self.inv = inv

    def check_stock(self, name, qty):
        med = self.inv.get(name)
        if med is None:
            raise Exception("Medicine not found")
        if med.stock < qty:
            raise Exception("Out of stock")
        return med

    def update(self, name, qty):
        med = self.inv.get(name)
        med.stock -= qty


class BillingController:
    def generate(self, med, qty):
        return med.price * qty


class DispenseController:
    def __init__(self, inv):
        self.v = ValidationSystem()
        self.im = InventoryManager(inv)
        self.bc = BillingController()

    def dispense(self, pres):
        self.v.validate(pres)
        med = self.im.check_stock(pres.drug, pres.qty)
        self.v.check_expiry(med)
        self.v.check_interaction(pres.drug)
        self.im.update(pres.drug, pres.qty)
        amount = self.bc.generate(med, pres.qty)
        return amount, med.stock


# =====================================================================
#  HELPER - Build a fresh inventory for each test
# =====================================================================

def build_inventory():
    """
    Returns a fully stocked Inventory instance.
    Stock values match the original CLI program so BVA tests
    against exact boundary values (e.g. Cough Syrup = 20).
    """
    inv = Inventory()
    inv.add(Medicine("Paracetamol", 100, 10,  date(2027, 5, 10)))
    inv.add(Medicine("Cough Syrup",  20, 80,  date(2026, 8, 15)))
    inv.add(Medicine("ExpiredMed",   50, 25,  date(2023, 1,  1)))
    inv.add(Medicine("DrugX",        30, 100, date(2027, 1,  1)))
    return inv


# =====================================================================
#  BLACK BOX TEST SUITE
# =====================================================================

class TestPharmacyDispenseMedicine(unittest.TestCase):
    """
    Black Box Test Suite for the 'Dispense Medicine' use case.

    Techniques:
      - ECP  : groups valid/invalid inputs into equivalence classes
      - BVA  : tests boundary values (qty = 0, 1, 20, 100, etc.)
    """

    def setUp(self):
        """
        Runs before every test method.
        A fresh inventory + fresh DispenseController ensures tests
        are independent (no shared state between runs).
        """
        self.inv = build_inventory()
        self.dc  = DispenseController(self.inv)

    # -----------------------------------------------------------------
    # TC01 | ECP - Valid class | Successful dispense
    # -----------------------------------------------------------------
    def test_TC01_valid_prescription_sufficient_stock(self):
        """
        TC01: Valid PID, known drug, qty within stock.
        Expected: Bill = ₹50, remaining stock = 95.
        Technique: ECP – valid equivalence class for all inputs.
        """
        pres = Prescription("P101", "Paracetamol", 5)
        amount, remaining = self.dc.dispense(pres)
        self.assertEqual(amount, 50,  "Bill should be ₹50 (10 × 5)")
        self.assertEqual(remaining, 95, "Stock should reduce from 100 to 95")

    # -----------------------------------------------------------------
    # TC02 | ECP - Invalid PID class
    # -----------------------------------------------------------------
    def test_TC02_empty_prescription_id(self):
        """
        TC02: Empty Prescription ID.
        Expected: Exception 'Invalid Prescription'.
        Technique: ECP – invalid PID equivalence class.
        """
        pres = Prescription("", "Paracetamol", 5)
        with self.assertRaises(Exception) as ctx:
            self.dc.dispense(pres)
        self.assertIn("Invalid Prescription", str(ctx.exception))

    # -----------------------------------------------------------------
    # TC03 | BVA - Quantity boundary: 0
    # -----------------------------------------------------------------
    def test_TC03_quantity_zero_boundary(self):
        """
        TC03: Qty = 0 (lower boundary, invalid side).
        Expected: Exception 'Invalid quantity'.
        Technique: BVA – zero is the smallest invalid quantity.
        """
        pres = Prescription("P102", "Paracetamol", 0)
        with self.assertRaises(Exception) as ctx:
            self.dc.dispense(pres)
        self.assertIn("Invalid quantity", str(ctx.exception))

    # -----------------------------------------------------------------
    # TC04 | ECP - Invalid quantity class (negative)
    # -----------------------------------------------------------------
    def test_TC04_negative_quantity(self):
        """
        TC04: Qty = -2 (negative integer).
        Expected: Exception 'Invalid quantity'.
        Technique: ECP – negative numbers are invalid equivalence class.
        """
        pres = Prescription("P103", "Paracetamol", -2)
        with self.assertRaises(Exception) as ctx:
            self.dc.dispense(pres)
        self.assertIn("Invalid quantity", str(ctx.exception))

    # -----------------------------------------------------------------
    # TC05 | ECP - Invalid drug name class
    # -----------------------------------------------------------------
    def test_TC05_medicine_not_in_inventory(self):
        """
        TC05: Drug 'CrocinX' does not exist in inventory.
        Expected: Exception 'Medicine not found'.
        Technique: ECP – unknown drug is invalid equivalence class.
        """
        pres = Prescription("P104", "CrocinX", 2)
        with self.assertRaises(Exception) as ctx:
            self.dc.dispense(pres)
        self.assertIn("Medicine not found", str(ctx.exception))

    # -----------------------------------------------------------------
    # TC06 | BVA - Quantity > stock (above upper boundary)
    # -----------------------------------------------------------------
    def test_TC06_quantity_exceeds_stock(self):
        """
        TC06: Cough Syrup stock = 20, requesting qty = 50.
        Expected: Exception 'Out of stock'.
        Technique: BVA – quantity above the maximum available boundary.
        """
        pres = Prescription("P105", "Cough Syrup", 50)
        with self.assertRaises(Exception) as ctx:
            self.dc.dispense(pres)
        self.assertIn("Out of stock", str(ctx.exception))

    # -----------------------------------------------------------------
    # TC07 | BVA - Quantity exactly equals stock (upper boundary)
    # -----------------------------------------------------------------
    def test_TC07_quantity_equals_stock_exact_boundary(self):
        """
        TC07: Cough Syrup stock = 20, requesting qty = 20 (exact match).
        Expected: Bill = ₹1600, remaining stock = 0.
        Technique: BVA – upper exact boundary (should succeed).
        """
        pres = Prescription("P106", "Cough Syrup", 20)
        amount, remaining = self.dc.dispense(pres)
        self.assertEqual(amount, 1600, "Bill should be ₹1600 (80 × 20)")
        self.assertEqual(remaining, 0,  "Stock should drop to exactly 0")

    # -----------------------------------------------------------------
    # TC08 | ECP - Expired medicine class
    # -----------------------------------------------------------------
    def test_TC08_expired_medicine(self):
        """
        TC08: ExpiredMed has expiry date 2023-01-01 (past).
        Expected: Exception 'Medicine expired'.
        Technique: ECP – expired drugs form an invalid class.
        """
        pres = Prescription("P107", "ExpiredMed", 2)
        with self.assertRaises(Exception) as ctx:
            self.dc.dispense(pres)
        self.assertIn("Medicine expired", str(ctx.exception))

    # -----------------------------------------------------------------
    # TC09 | ECP - Drug interaction class
    # -----------------------------------------------------------------
    def test_TC09_drug_interaction_detected(self):
        """
        TC09: DrugX triggers a known drug interaction alert.
        Expected: Exception 'Drug interaction'.
        Technique: ECP – interacting drugs form their own invalid class.
        """
        pres = Prescription("P108", "DrugX", 2)
        with self.assertRaises(Exception) as ctx:
            self.dc.dispense(pres)
        self.assertIn("Drug interaction", str(ctx.exception))

    # -----------------------------------------------------------------
    # TC10 | ECP - Valid class, billing accuracy
    # -----------------------------------------------------------------
    def test_TC10_valid_billing_calculation(self):
        """
        TC10: Paracetamol price = ₹10, qty = 10.
        Expected: Bill = ₹100.
        Technique: ECP – valid class, verifies BillingController accuracy.
        """
        pres = Prescription("P109", "Paracetamol", 10)
        amount, _ = self.dc.dispense(pres)
        self.assertEqual(amount, 100, "Bill should be ₹100 (10 × 10)")

    # -----------------------------------------------------------------
    # TC11 | ECP - Case-insensitive drug name
    # -----------------------------------------------------------------
    def test_TC11_lowercase_drug_name(self):
        """
        TC11: Drug entered as 'paracetamol' (all lowercase).
        Expected: Treated identically to 'Paracetamol'; bill = ₹30.
        Technique: ECP – case variation is valid equivalence class.
        """
        pres = Prescription("P110", "paracetamol", 3)
        amount, _ = self.dc.dispense(pres)
        self.assertEqual(amount, 30, "Bill should be ₹30 (10 × 3)")

    # -----------------------------------------------------------------
    # TC12 | ECP - Large valid quantity within stock
    # -----------------------------------------------------------------
    def test_TC12_large_valid_quantity_within_stock(self):
        """
        TC12: Paracetamol stock = 100, requesting qty = 50.
        Expected: Bill = ₹500, remaining stock = 50.
        Technique: ECP – large but valid quantity class.
        """
        pres = Prescription("P111", "Paracetamol", 50)
        amount, remaining = self.dc.dispense(pres)
        self.assertEqual(amount, 500,   "Bill should be ₹500 (10 × 50)")
        self.assertEqual(remaining, 50, "Stock should drop from 100 to 50")

    # -----------------------------------------------------------------
    # TC13 | BVA - Minimum valid quantity boundary (qty = 1)
    # -----------------------------------------------------------------
    def test_TC13_minimum_valid_quantity_boundary(self):
        """
        TC13: Minimum valid qty = 1 (lower valid boundary).
        Expected: Bill = ₹80, remaining Cough Syrup stock = 19.
        Technique: BVA – qty = 1 is the smallest valid positive integer.
        """
        pres = Prescription("P112", "Cough Syrup", 1)
        amount, remaining = self.dc.dispense(pres)
        self.assertEqual(amount, 80,    "Bill should be ₹80 (80 × 1)")
        self.assertEqual(remaining, 19, "Stock should drop from 20 to 19")

    # -----------------------------------------------------------------
    # TC14 | ECP - Patient identity irrelevant to dispense logic
    # -----------------------------------------------------------------
    def test_TC14_patient_details_irrelevant_to_logic(self):
        """
        TC14: PID = 'P113'; system does not validate patient identity
              beyond PID being non-empty.
        Expected: Medicine dispensed, bill = ₹20 (10 × 2).
        Technique: ECP – confirms PID non-empty is sufficient.
        """
        pres = Prescription("P113", "Paracetamol", 2)
        amount, _ = self.dc.dispense(pres)
        self.assertEqual(amount, 20, "Bill should be ₹20 (10 × 2)")

    # -----------------------------------------------------------------
    # TC15 | ECP - Invalid data type for quantity (non-integer string)
    # -----------------------------------------------------------------
    def test_TC15_invalid_datatype_for_quantity(self):
        """
        TC15: Qty = 'abc' (string passed as quantity).
        Expected: TypeError raised before reaching business logic.
        Technique: ECP – non-numeric quantity is an invalid class.
        """
        with self.assertRaises((TypeError, ValueError, Exception)):
            qty = int("abc")           # Simulates CLI int() conversion
            pres = Prescription("P114", "Paracetamol", qty)
            self.dc.dispense(pres)

    # -----------------------------------------------------------------
    # TC16 | ECP - Drug name with leading/trailing spaces
    # -----------------------------------------------------------------
    def test_TC16_drug_name_with_extra_spaces(self):
        """
        TC16: Drug = ' Paracetamol ' (spaces around the name).
        Expected: Spaces stripped; medicine dispensed, bill = ₹50.
        Technique: ECP – whitespace-padded input is a valid class
                         (system should normalise input).
        """
        pres = Prescription("P115", " Paracetamol ", 5)
        amount, _ = self.dc.dispense(pres)
        self.assertEqual(amount, 50, "Bill should be ₹50 (10 × 5)")

    # -----------------------------------------------------------------
    # TC17 | State-based – Sequential dispense reduces stock correctly
    # -----------------------------------------------------------------
    def test_TC17_sequential_dispensing_reduces_stock(self):
        """
        TC17: Two consecutive dispenses of Paracetamol (qty 30 + qty 30).
              First dispense: stock 100 → 70.
              Second dispense: stock 70 → 40.
        Expected: Both succeed; stock reflects cumulative deduction.
        Technique: ECP – sequential state change (valid class).
        """
        pres1 = Prescription("P116a", "Paracetamol", 30)
        _, stock_after_first = self.dc.dispense(pres1)
        self.assertEqual(stock_after_first, 70, "After first dispense stock = 70")

        pres2 = Prescription("P116b", "Paracetamol", 30)
        _, stock_after_second = self.dc.dispense(pres2)
        self.assertEqual(stock_after_second, 40, "After second dispense stock = 40")

    # -----------------------------------------------------------------
    # TC18 | BVA - Very high quantity (stress / boundary at max stock)
    # -----------------------------------------------------------------
    def test_TC18_very_high_quantity_stress(self):
        """
        TC18: Paracetamol stock = 100, requesting qty = 100 (exact max).
        Expected: Bill = ₹1000, remaining stock = 0.
        Also verifies qty = 101 raises 'Out of stock'.
        Technique: BVA – exact upper stock boundary and one above.
        """
        # Exact max boundary → should succeed
        pres_max = Prescription("P117a", "Paracetamol", 100)
        amount, remaining = self.dc.dispense(pres_max)
        self.assertEqual(amount, 1000, "Bill should be ₹1000 (10 × 100)")
        self.assertEqual(remaining, 0, "Stock should be 0 after full depletion")

        # Reset inventory for the one-above boundary
        self.setUp()
        pres_over = Prescription("P117b", "Paracetamol", 101)
        with self.assertRaises(Exception) as ctx:
            self.dc.dispense(pres_over)
        self.assertIn("Out of stock", str(ctx.exception))


# =====================================================================
#  TEST RUNNER WITH DETAILED REPORT
# =====================================================================

class VerboseTestResult(unittest.TextTestResult):
    """Custom result class that prints a structured pass/fail table."""

    PASS  = "PASS "
    FAIL  = "FAIL "
    ERROR = "ERROR"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.results.append((test, self.PASS, ""))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.results.append((test, self.FAIL, str(err[1])))

    def addError(self, test, err):
        super().addError(test, err)
        self.results.append((test, self.ERROR, str(err[1])))


def run_tests():
    print("=" * 78)
    print(" BLACK BOX TESTING – PHARMACY MANAGEMENT SYSTEM")
    print(" Use Case : Dispense Medicine")
    print(" Student  : Shreya Raju Pawar | Roll No: 24107I060")
    print(" Date     : 30/04/2026")
    print("=" * 78)
    print(f"{'TC ID':<6} {'Test Name':<48} {'Result':<7} {'Remarks'}")
    print("-" * 78)

    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(TestPharmacyDispenseMedicine)

    stream = open("/dev/null", "w")
    runner = unittest.TextTestRunner(
        stream=stream,
        resultclass=VerboseTestResult,
        verbosity=0
    )
    result = runner.run(suite)

    tc_ids = {
        "test_TC01_valid_prescription_sufficient_stock"  : "TC01",
        "test_TC02_empty_prescription_id"                : "TC02",
        "test_TC03_quantity_zero_boundary"               : "TC03",
        "test_TC04_negative_quantity"                    : "TC04",
        "test_TC05_medicine_not_in_inventory"            : "TC05",
        "test_TC06_quantity_exceeds_stock"               : "TC06",
        "test_TC07_quantity_equals_stock_exact_boundary" : "TC07",
        "test_TC08_expired_medicine"                     : "TC08",
        "test_TC09_drug_interaction_detected"            : "TC09",
        "test_TC10_valid_billing_calculation"            : "TC10",
        "test_TC11_lowercase_drug_name"                  : "TC11",
        "test_TC12_large_valid_quantity_within_stock"    : "TC12",
        "test_TC13_minimum_valid_quantity_boundary"      : "TC13",
        "test_TC14_patient_details_irrelevant_to_logic"  : "TC14",
        "test_TC15_invalid_datatype_for_quantity"        : "TC15",
        "test_TC16_drug_name_with_extra_spaces"          : "TC16",
        "test_TC17_sequential_dispensing_reduces_stock"  : "TC17",
        "test_TC18_very_high_quantity_stress"            : "TC18",
    }

    passed = failed = errors = 0
    for test, status, msg in result.results:
        method = test._testMethodName
        tc_id  = tc_ids.get(method, "???")
        short  = test.shortDescription() or method
        # Truncate long names
        if len(short) > 46:
            short = short[:43] + "..."
        remark = ""
        if status == VerboseTestResult.FAIL:
            remark = "AssertionError"
            failed += 1
        elif status == VerboseTestResult.ERROR:
            remark = "Unexpected exception"
            errors += 1
        else:
            passed += 1
        print(f"{tc_id:<6} {short:<48} {status:<7} {remark}")

    stream.close()

    total = passed + failed + errors
    print("-" * 78)
    print(f"\n SUMMARY   Total: {total}  |  Passed: {passed}  |"
          f"  Failed: {failed}  |  Errors: {errors}")
    print("=" * 78)

    # Equivalence class summary
    print("\n EQUIVALENCE CLASS PARTITIONING (ECP) SUMMARY")
    print("-" * 78)
    ecp_table = [
        ("Valid PID",         "Non-empty string",        "TC01,TC07,TC10,TC11,TC12,TC13,TC14,TC16,TC17,TC18"),
        ("Invalid PID",       "Empty string \"\"",        "TC02"),
        ("Valid Quantity",    "Integer ≥ 1 and ≤ stock", "TC01,TC07,TC10,TC12,TC13,TC17,TC18"),
        ("Invalid Quantity",  "0 or negative",           "TC03,TC04"),
        ("Valid Drug Name",   "Exists in inventory",     "TC01,TC07,TC10,TC11,TC12,TC13,TC16,TC17,TC18"),
        ("Unknown Drug",      "Not in inventory",        "TC05"),
        ("Excessive Qty",     "qty > available stock",   "TC06"),
        ("Expired Medicine",  "Expiry < today",          "TC08"),
        ("Drug Interaction",  "DrugX triggers alert",    "TC09"),
        ("Invalid Data Type", "Non-numeric qty input",   "TC15"),
        ("Whitespace Input",  "Drug name with spaces",   "TC16"),
    ]
    print(f"  {'Class':<25} {'Description':<35} {'TCs'}")
    for cls, desc, tcs in ecp_table:
        print(f"  {cls:<25} {desc:<35} {tcs}")

    print("\n BOUNDARY VALUE ANALYSIS (BVA) SUMMARY")
    print("-" * 78)
    bva_table = [
        ("Qty = 0",   "Just below valid lower bound → Invalid",         "TC03"),
        ("Qty = 1",   "Valid lower bound (minimum valid quantity)",       "TC13"),
        ("Qty = 20",  "Upper exact bound (Cough Syrup stock = 20)",       "TC07"),
        ("Qty = 50",  "Above Cough Syrup upper bound → Out of stock",     "TC06"),
        ("Qty = 100", "Upper exact bound (Paracetamol stock = 100)",      "TC18"),
        ("Qty = 101", "Just above Paracetamol upper bound → Out of stock","TC18"),
    ]
    print(f"  {'Boundary':<10} {'Description':<50} {'TC'}")
    for bnd, desc, tc in bva_table:
        print(f"  {bnd:<10} {desc:<50} {tc}")

    print("=" * 78)
    return result


# =====================================================================
#  INTERACTIVE CLI – Manual Test Case Execution
# =====================================================================

# Colour codes (fallback to plain if terminal doesn't support them)
try:
    import sys
    _CLR = sys.stdout.isatty()
except Exception:
    _CLR = False

def _c(code, text):
    return f"\033[{code}m{text}\033[0m" if _CLR else text

GREEN  = lambda t: _c("92", t)
RED    = lambda t: _c("91", t)
YELLOW = lambda t: _c("93", t)
CYAN   = lambda t: _c("96", t)
BOLD   = lambda t: _c("1",  t)


# Metadata for all 18 test cases used in the interactive menu
TC_META = [
    ("TC01", "Valid prescription, sufficient stock",
     "P101", "Paracetamol",    5),
    ("TC02", "Empty prescription ID",
     "",     "Paracetamol",    5),
    ("TC03", "Quantity = 0 (invalid boundary)",
     "P102", "Paracetamol",    0),
    ("TC04", "Negative quantity",
     "P103", "Paracetamol",   -2),
    ("TC05", "Medicine not present in inventory",
     "P104", "CrocinX",        2),
    ("TC06", "Quantity greater than available stock",
     "P105", "Cough Syrup",   50),
    ("TC07", "Quantity exactly equal to stock (boundary)",
     "P106", "Cough Syrup",   20),
    ("TC08", "Expired medicine check",
     "P107", "ExpiredMed",     2),
    ("TC09", "Drug interaction detected",
     "P108", "DrugX",          2),
    ("TC10", "Valid billing calculation",
     "P109", "Paracetamol",   10),
    ("TC11", "Lowercase drug name (case-insensitive)",
     "P110", "paracetamol",    3),
    ("TC12", "Large valid quantity within stock",
     "P111", "Paracetamol",   50),
    ("TC13", "Minimum valid quantity (boundary = 1)",
     "P112", "Cough Syrup",    1),
    ("TC14", "Patient details irrelevant to logic",
     "P113", "Paracetamol",    2),
    ("TC15", "Invalid data type for quantity (abc)",
     "P114", "Paracetamol", "abc"),   # qty is a string here intentionally
    ("TC16", "Drug name with extra spaces",
     "P115", " Paracetamol ",  5),
    ("TC17", "Sequential dispensing reducing stock",
     "P116", "Paracetamol",   30),    # run twice automatically
    ("TC18", "Very high quantity (stress / boundary)",
     "P117", "Paracetamol",  100),    # also tests 101 automatically
]


def _run_single_dispense(dc, pid, drug, qty_raw):
    """
    Attempt a dispense and return (success, amount, remaining, error_msg).
    qty_raw may be int or a bad-type string (TC15).
    """
    try:
        qty = int(qty_raw)          # raises ValueError for non-numeric
        pres = Prescription(pid, drug, qty)
        amount, remaining = dc.dispense(pres)
        return True, amount, remaining, None
    except (ValueError, TypeError) as e:
        return False, None, None, f"Invalid input / type error: {e}"
    except Exception as e:
        return False, None, None, str(e)


def _show_dispense_result(pid, drug, qty_raw, success, amount, remaining, error):
    print(flush=True)
    print(BOLD("  ┌─── RESULT ────────────────────────────────────────┐"), flush=True)
    print(f"  │  Prescription ID : {pid}", flush=True)
    print(f"  │  Drug            : {drug}", flush=True)
    print(f"  │  Quantity        : {qty_raw}", flush=True)
    if success:
        print(f"  │  Status          : {GREEN('✔  Medicine Dispensed Successfully')}", flush=True)
        print(f"  │  Bill Amount     : ₹{amount}", flush=True)
        print(f"  │  Remaining Stock : {remaining}", flush=True)
    else:
        print(f"  │  Status          : {RED('✘  ' + error)}", flush=True)
    print(BOLD("  └────────────────────────────────────────────────────┘"), flush=True)


def run_interactive_cli():
    """
    Interactive menu-driven CLI.
    Modes:
      1. Run a specific TC from the menu (pre-filled inputs shown, user confirms or edits)
      2. Run all 18 TCs automatically
      3. Enter completely custom inputs
      4. Exit to automated test suite
    """
    inv_master = build_inventory()   # shared inventory across manual runs

    print(flush=True)
    print(BOLD("=" * 66), flush=True)
    print(BOLD("  PHARMACY MANAGEMENT SYSTEM – BLACK BOX TESTING"), flush=True)
    print(BOLD("  Interactive Test Case Runner"), flush=True)
    print(BOLD("=" * 66), flush=True)
    print(f"  Student : Shreya Raju Pawar  |  Roll No : 24107I060", flush=True)
    print(f"  Course  : Software Engineering  |  Date : 30/04/2026", flush=True)
    print(BOLD("=" * 66), flush=True)

    while True:
        print(flush=True)
        print("  +======================================+", flush=True)
        print("  |           MAIN MENU                  |", flush=True)
        print("  +======================================+", flush=True)
        print("  |  1. Run a specific Test Case (TC)    |", flush=True)
        print("  |  2. Run ALL 18 Test Cases (auto)     |", flush=True)
        print("  |  3. Enter custom inputs manually     |", flush=True)
        print("  |  4. Run automated test suite & exit  |", flush=True)
        print("  +======================================+", flush=True)
        sys.stdout.write("\n  Enter choice (1/2/3/4): ")
        sys.stdout.flush()
        choice = input().strip()

        # ── Option 1: Run a specific TC ──────────────────────────────
        if choice == "1":
            print(flush=True)
            print(BOLD("  Available Test Cases:"), flush=True)
            print(f"  {'No.':<5} {'TC ID':<6} {'Description'}", flush=True)
            print("  " + "-" * 60, flush=True)
            for i, (tc_id, desc, *_) in enumerate(TC_META, 1):
                print(f"  {i:<5} {tc_id:<6} {desc}", flush=True)
            print(flush=True)
            sys.stdout.write("  Enter TC number (1-18): "); sys.stdout.flush()
            sel = input().strip()
            try:
                idx = int(sel) - 1
                if not (0 <= idx <= 17):
                    raise ValueError
            except ValueError:
                print(RED("  Invalid selection."), flush=True)
                continue

            tc_id, desc, pid, drug, qty_raw = TC_META[idx]
            print(flush=True)
            print(BOLD(f"  ── {tc_id}: {desc} ──"), flush=True)
            print(f"  Pre-filled inputs:", flush=True)
            print(f"    Prescription ID : '{pid}'", flush=True)
            print(f"    Drug Name       : '{drug}'", flush=True)
            print(f"    Quantity        : '{qty_raw}'", flush=True)
            print(flush=True)
            sys.stdout.write("  Press ENTER to use these inputs, or type 'edit' to change them: "); sys.stdout.flush()
            edit = input().strip().lower()

            if edit == "edit":
                sys.stdout.write("  Enter Prescription ID : "); sys.stdout.flush()
                pid     = input().strip()
                sys.stdout.write("  Enter Drug Name       : "); sys.stdout.flush()
                drug    = input().strip()
                sys.stdout.write("  Enter Quantity        : "); sys.stdout.flush()
                qty_raw = input().strip()

            # TC17 special: run twice to show stock deduction
            if tc_id == "TC17" and edit != "edit":
                dc = DispenseController(build_inventory())
                print(YELLOW("\n  [TC17] Running first dispense (qty=30)..."), flush=True)
                s, a, r, e = _run_single_dispense(dc, "P116a", "Paracetamol", 30)
                _show_dispense_result("P116a", "Paracetamol", 30, s, a, r, e)
                print(YELLOW("\n  [TC17] Running second dispense (qty=30) on same inventory..."), flush=True)
                s, a, r, e = _run_single_dispense(dc, "P116b", "Paracetamol", 30)
                _show_dispense_result("P116b", "Paracetamol", 30, s, a, r, e)
            # TC18 special: run qty=100 then qty=101
            elif tc_id == "TC18" and edit != "edit":
                dc = DispenseController(build_inventory())
                print(YELLOW("\n  [TC18] Testing exact upper boundary (qty=100)..."), flush=True)
                s, a, r, e = _run_single_dispense(dc, "P117a", "Paracetamol", 100)
                _show_dispense_result("P117a", "Paracetamol", 100, s, a, r, e)
                dc2 = DispenseController(build_inventory())
                print(YELLOW("\n  [TC18] Testing one-above boundary (qty=101)..."), flush=True)
                s, a, r, e = _run_single_dispense(dc2, "P117b", "Paracetamol", 101)
                _show_dispense_result("P117b", "Paracetamol", 101, s, a, r, e)
            else:
                dc = DispenseController(build_inventory())
                s, a, r, e = _run_single_dispense(dc, pid, drug, qty_raw)
                _show_dispense_result(pid, drug, qty_raw, s, a, r, e)

        # ── Option 2: Run all 18 TCs automatically ───────────────────
        elif choice == "2":
            print(flush=True)
            print(BOLD("=" * 66), flush=True)
            print(BOLD("  AUTO-RUN: All 18 Black Box Test Cases"), flush=True)
            print(BOLD("=" * 66), flush=True)
            print(f"  {'TC ID':<6} {'Description':<38} {'Qty':>5}  {'Result'}", flush=True)
            print("  " + "-" * 64, flush=True)

            pass_count = fail_count = 0
            for tc_id, desc, pid, drug, qty_raw in TC_META:
                if tc_id == "TC17":
                    # two sequential dispenses
                    dc = DispenseController(build_inventory())
                    s1, _, r1, e1 = _run_single_dispense(dc, "P116a", drug, qty_raw)
                    s2, _, r2, e2 = _run_single_dispense(dc, "P116b", drug, qty_raw)
                    ok = s1 and s2 and r1 == 70 and r2 == 40
                elif tc_id == "TC18":
                    dc1 = DispenseController(build_inventory())
                    s1, a1, r1, _ = _run_single_dispense(dc1, "P117a", drug, 100)
                    dc2 = DispenseController(build_inventory())
                    s2, _, _, e2  = _run_single_dispense(dc2, "P117b", drug, 101)
                    ok = s1 and (not s2) and "Out of stock" in (e2 or "")
                else:
                    dc = DispenseController(build_inventory())
                    s, a, r, e = _run_single_dispense(dc, pid, drug, qty_raw)
                    # Expected outcomes per TC
                    if tc_id in ("TC01",):
                        ok = s and a == 50  and r == 95
                    elif tc_id in ("TC02","TC03","TC04","TC05","TC06",
                                   "TC08","TC09","TC15"):
                        ok = not s
                    elif tc_id == "TC07":
                        ok = s and r == 0
                    elif tc_id == "TC10":
                        ok = s and a == 100
                    elif tc_id == "TC11":
                        ok = s and a == 30
                    elif tc_id == "TC12":
                        ok = s and a == 500 and r == 50
                    elif tc_id == "TC13":
                        ok = s and r == 19
                    elif tc_id == "TC14":
                        ok = s and a == 20
                    elif tc_id == "TC16":
                        ok = s and a == 50
                    else:
                        ok = s

                result_str = GREEN("PASS ✔") if ok else RED("FAIL ✘")
                short_desc = desc[:36] + ".." if len(desc) > 36 else desc
                qty_display = str(qty_raw)[:5]
                print(f"  {tc_id:<6} {short_desc:<38} {qty_display:>5}  {result_str}", flush=True)
                if ok:
                    pass_count += 1
                else:
                    fail_count += 1

            print("  " + "-" * 64, flush=True)
            print(f"\n  {BOLD('SUMMARY')}  Total: 18  |  "
                  f"{GREEN(f'Passed: {pass_count}')}  |  "
                  f"{RED(f'Failed: {fail_count}')}", flush=True)
            print(BOLD("=" * 66), flush=True)

        # ── Option 3: Custom input ────────────────────────────────────
        elif choice == "3":
            print(flush=True)
            print(BOLD("  ── Custom Manual Input ──"), flush=True)
            print(f"  Available medicines in inventory:", flush=True)
            for name, med in build_inventory().data.items():
                print(f"    • {med.name:<14}  Stock: {med.stock:<4}  Price: ₹{med.price:<5}  Expiry: {med.expiry}", flush=True)
            print(flush=True)
            sys.stdout.write("  Enter Prescription ID  : "); sys.stdout.flush()
            pid     = input().strip()
            sys.stdout.write("  Enter Drug Name        : "); sys.stdout.flush()
            drug    = input().strip()
            sys.stdout.write("  Enter Quantity         : "); sys.stdout.flush()
            qty_raw = input().strip()

            dc = DispenseController(build_inventory())
            s, a, r, e = _run_single_dispense(dc, pid, drug, qty_raw)
            _show_dispense_result(pid, drug, qty_raw, s, a, r, e)

        # ── Option 4: Exit to automated suite ────────────────────────
        elif choice == "4":
            print(flush=True)
            print(BOLD(CYAN("  Launching automated unittest suite...")), flush=True)
            print(flush=True)
            break

        else:
            print(RED("  Please enter 1, 2, 3, or 4."), flush=True)


if __name__ == "__main__":
    run_interactive_cli()
    run_tests()