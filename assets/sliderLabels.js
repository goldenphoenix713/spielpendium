/**
 * Custom label formatters for Spielpendium range sliders.
 * DMC resolves functions-as-props from window.dashMantineFunctions.
 * Referenced in Python via: label={"function": "yearFormatter"}
 */
window.dashMantineFunctions = window.dashMantineFunctions || {};

/**
 * Year slider: show "≤1970" when at the floor, otherwise the plain year.
 */
window.dashMantineFunctions.yearFormatter = function (value) {
    if (value <= 1970) return "\u22641970";
    return String(value);
};

/**
 * Players slider: show "10+" at the max, otherwise the plain number.
 */
window.dashMantineFunctions.playersFormatter = function (value) {
    if (value >= 10) return "10+";
    return String(value);
};

/**
 * Play time slider: show "240+" at the cap, otherwise the plain minutes.
 */
window.dashMantineFunctions.playTimeFormatter = function (value) {
    if (value >= 240) return "240+";
    return String(value);
};

/**
 * Age slider: show "18+" at the cap, otherwise the plain age.
 */
window.dashMantineFunctions.ageFormatter = function (value) {
    if (value >= 18) return "18+";
    return String(value);
};
