import unittest

from bidding import binary

class TestBinaryModule(unittest.TestCase):
    def test_parse_hand_f(self):
        # Test that the function returns the correct value
        hand_str = 'KJT83.86.632.Q62'
        hand52 = binary.parse_hand_f(52)(hand_str).reshape(52)
        expected_result = [0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1]
        self.assertEqual(hand52.tolist(), expected_result)

if __name__ == '__main__':
    unittest.main()