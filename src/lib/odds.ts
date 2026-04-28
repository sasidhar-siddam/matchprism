/**
 * Odds conversion and value analysis utilities.
 * Pure math — no external dependencies or API calls.
 */

/** Convert decimal odds to implied probability (%). */
export function decimalToImplied(decimal: number): number {
  return (1 / decimal) * 100;
}

/** Convert implied probability (%) to decimal odds. */
export function impliedToDecimal(prob: number): number {
  if (prob <= 0) return Infinity;
  return 100 / prob;
}

/** Convert fractional odds (e.g., 40/1) to decimal. */
export function fractionalToDecimal(num: number, den: number): number {
  return num / den + 1;
}

/** Convert American odds to decimal. */
export function americanToDecimal(american: number): number {
  if (american > 0) return american / 100 + 1;
  return 100 / Math.abs(american) + 1;
}

/** Format decimal odds as a fractional string (e.g., 41.00 -> "40/1"). */
export function decimalToFractional(decimal: number): string {
  const fraction = decimal - 1;
  if (fraction < 1) {
    // Odds-on: try common denominators
    for (const den of [1, 2, 3, 4, 5, 6, 8, 10]) {
      const num = Math.round(fraction * den);
      if (num > 0 && Math.abs(fraction - num / den) < 0.03) {
        return `${num}/${den}`;
      }
    }
    return `${fraction.toFixed(1)}/1`;
  }
  // Odds-against
  for (const den of [1, 2, 4, 5]) {
    const num = Math.round(fraction * den);
    if (Math.abs(fraction - num / den) < 0.05) {
      return `${num}/${den}`;
    }
  }
  return `${Math.round(fraction)}/1`;
}

/** Calculate edge: model probability minus bookmaker implied probability. */
export function calcEdge(modelProb: number, impliedProb: number): number {
  return modelProb - impliedProb;
}

/**
 * Kelly criterion: mathematically optimal fraction of bankroll to stake.
 * Returns a value between 0 and 1 (0% to 100% of bankroll).
 */
export function kellyFraction(modelProb: number, decimalOdds: number): number {
  const p = modelProb / 100;
  const b = decimalOdds - 1;
  const q = 1 - p;
  const kelly = (p * b - q) / b;
  return Math.max(0, kelly);
}

/**
 * Quarter-Kelly: a more conservative stake sizing.
 * Most professionals use 1/4 Kelly to reduce variance.
 */
export function quarterKelly(modelProb: number, decimalOdds: number): number {
  return kellyFraction(modelProb, decimalOdds) / 4;
}

/** Classify value opportunity based on edge percentage. */
export function getVerdict(edge: number): "VALUE" | "FAIR" | "AVOID" {
  if (edge > 3) return "VALUE";
  if (edge > -2) return "FAIR";
  return "AVOID";
}

/** Expected value per unit staked (e.g., per $1). */
export function expectedValue(modelProb: number, decimalOdds: number): number {
  const p = modelProb / 100;
  return p * (decimalOdds - 1) - (1 - p);
}
