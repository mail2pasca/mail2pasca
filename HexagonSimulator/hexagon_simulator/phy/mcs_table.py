# A simplified MCS table mapping SINR (dB) to modulation order and coding rate.
# Format: (min_sinr_db, modulation_order, coding_rate)
# Modulation order: 2=QPSK, 4=16QAM, 6=64QAM, 8=256QAM
MCS_TABLE = [
    (-5.0, 2, 0.2),  # QPSK
    (0.0,  2, 0.4),
    (5.0,  4, 0.4),  # 16QAM
    (10.0, 4, 0.6),
    (15.0, 6, 0.6),  # 64QAM
    (20.0, 6, 0.8),
    (25.0, 8, 0.8),  # 256QAM
    (30.0, 8, 0.9)
]
