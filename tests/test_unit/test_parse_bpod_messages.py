import pytest

from village.scripts.parse_bpod_messages import (
    parse_input_to_tuple_override,
    parse_output_to_tuple,
    parse_output_to_tuple_override,
)

# ── parse_input_to_tuple_override ────────────────────────────────────────────


class TestParseInput:
    def test_port_in(self):
        assert parse_input_to_tuple_override("Port1In") == ("Port", 1, 1)

    def test_port_out(self):
        assert parse_input_to_tuple_override("Port3Out") == ("Port", 3, 0)

    def test_port_channel_9(self):
        assert parse_input_to_tuple_override("Port9In") == ("Port", 9, 1)

    def test_pa1_port_in(self):
        assert parse_input_to_tuple_override("PA1_Port2In") == ("PA1_Port", 2, 1)

    def test_pa1_port_out(self):
        assert parse_input_to_tuple_override("PA1_Port5Out") == ("PA1_Port", 5, 0)

    def test_bnc_high(self):
        assert parse_input_to_tuple_override("BNC1High") == ("BNC", 1, 3)

    def test_bnc_low(self):
        assert parse_input_to_tuple_override("BNC2Low") == ("BNC", 2, 0)

    def test_serial_single_digit_value(self):
        assert parse_input_to_tuple_override("Serial1_5") == ("Serial", 1, 5)

    def test_serial_two_digit_value(self):
        assert parse_input_to_tuple_override("Serial2_99") == ("Serial", 2, 99)

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_input_to_tuple_override("Unknown")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            parse_input_to_tuple_override("")

    def test_partial_match_raises(self):
        with pytest.raises(ValueError):
            parse_input_to_tuple_override("PortIn")  # missing channel number


# ── parse_output_to_tuple_override ───────────────────────────────────────────


class TestParseOutputOverride:
    def test_pwm(self):
        assert parse_output_to_tuple_override(("PWM1", 128)) == ("PWM", 1, 128)

    def test_pwm_zero(self):
        assert parse_output_to_tuple_override(("PWM2", 0)) == ("PWM", 2, 0)

    def test_valve_on(self):
        assert parse_output_to_tuple_override("Valve1") == ("Valve", 1, 1)

    def test_valve_off(self):
        assert parse_output_to_tuple_override("Valve3Off") == ("Valve", 3, 0)

    def test_valve_off_takes_priority_over_valve(self):
        # "Valve1Off" must match ValveOff pattern, not Valve pattern
        result = parse_output_to_tuple_override("Valve1Off")
        assert result == ("Valve", 1, 0)

    def test_bnc_high(self):
        assert parse_output_to_tuple_override("BNC1High") == ("BNC", 1, 3)

    def test_bnc_low(self):
        assert parse_output_to_tuple_override("BNC2Low") == ("BNC", 2, 0)

    def test_serial_tuple(self):
        assert parse_output_to_tuple_override(("Serial1", 7)) == ("Serial", 1, 7)

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_output_to_tuple_override("Unknown")


# ── parse_output_to_tuple ────────────────────────────────────────────────────


class TestParseOutputTuple:
    def test_tuple_passthrough(self):
        result = parse_output_to_tuple(("Valve", 1))
        assert result == ("Valve", 1)

    def test_valve_string(self):
        assert parse_output_to_tuple("Valve3") == ("Valve", 3)

    def test_bnc_high_string(self):
        assert parse_output_to_tuple("BNC1High") == ("BNC1", 3)

    def test_bnc_low_string(self):
        assert parse_output_to_tuple("BNC2Low") == ("BNC2", 0)

    def test_softcode(self):
        assert parse_output_to_tuple("SoftCode5") == ("SoftCode", 5)

    def test_global_timer_trig(self):
        assert parse_output_to_tuple("GlobalTimer1Trig") == ("GlobalTimerTrig", 1)

    def test_global_timer_cancel(self):
        assert parse_output_to_tuple("GlobalTimer2Cancel") == ("GlobalTimerCancel", 2)

    def test_global_counter_reset(self):
        assert parse_output_to_tuple("GlobalCounter3Reset") == ("GlobalCounterReset", 3)

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_output_to_tuple("BadMessage")
