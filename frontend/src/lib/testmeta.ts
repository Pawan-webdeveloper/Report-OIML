/** Mirror of the ruleset test_catalogue — display labels for kinds. */
export const TEST_META: Record<string, { formNo: string; title: string }> = {
  WEIGHING: { formNo: '1', title: 'Weighing performance' },
  TEMP_NOLOAD: { formNo: '2', title: 'Temperature effect on no-load' },
  ECC_WEIGHTS: { formNo: '3.1', title: 'Eccentricity (weights)' },
  ECC_ROLLING: { formNo: '3.2', title: 'Eccentricity (rolling load)' },
  DISC_DIGITAL: { formNo: '4.1.1', title: 'Discrimination (digital)' },
  DISC_ANALOG: { formNo: '4.1.2', title: 'Discrimination (analog)' },
  DISC_NONSELF: { formNo: '4.1.3', title: 'Discrimination (non-self-indicating)' },
  SENSITIVITY: { formNo: '4.2', title: 'Sensitivity' },
  REPEATABILITY: { formNo: '5', title: 'Repeatability' },
  ZERO_RETURN: { formNo: '6.1', title: 'Zero return' },
  CREEP: { formNo: '6.2', title: 'Creep' },
  STABILITY_EQ: { formNo: '7', title: 'Stability of equilibrium' },
  TILTING: { formNo: '8', title: 'Tilting' },
  TARE: { formNo: '9', title: 'Tare' },
  WARMUP: { formNo: '10', title: 'Warm-up time' },
  VOLTAGE: { formNo: '11', title: 'Voltage variation' },
  DIST_DIPS: { formNo: '12.1', title: 'Disturbance — voltage dips/interruptions' },
  DIST_BURST_MAINS: { formNo: '12.2a', title: 'Disturbance — EFT/burst (mains)' },
  DIST_BURST_IO: { formNo: '12.2b', title: 'Disturbance — EFT/burst (I/O)' },
  DIST_SURGE_AC: { formNo: '12.3a', title: 'Disturbance — surge (AC mains)' },
  DIST_SURGE_OTHER: { formNo: '12.3b', title: 'Disturbance — surge (other lines)' },
  DIST_ESD_DIRECT: { formNo: '12.4a', title: 'Disturbance — ESD (direct)' },
  DIST_ESD_INDIRECT: { formNo: '12.4b', title: 'Disturbance — ESD (indirect)' },
  DIST_RADIATED: { formNo: '12.5', title: 'Disturbance — radiated RF' },
  DIST_CONDUCTED_RF: { formNo: '12.6', title: 'Disturbance — conducted RF' },
  DIST_VEHICLE_SUPPLY: { formNo: '12.7a', title: 'Disturbance — vehicle supply' },
  DIST_VEHICLE_COUPLING: { formNo: '12.7b', title: 'Disturbance — vehicle coupling' },
  DAMP_HEAT: { formNo: '13', title: 'Damp heat, steady state' },
  SPAN_STABILITY: { formNo: '14', title: 'Span stability' },
  ENDURANCE: { formNo: '15', title: 'Endurance (always LAST — 3.10.1)' },
  CONSTRUCTION: { formNo: '16', title: 'Construction & fitment' },
  CHECKLIST: { formNo: '17', title: 'Checklist (17.1–17.4)' },
};

export const testTitle = (kind: string): string =>
  TEST_META[kind]?.title ?? kind.replaceAll('_', ' ');
export const testFormNo = (kind: string): string => TEST_META[kind]?.formNo ?? '—';