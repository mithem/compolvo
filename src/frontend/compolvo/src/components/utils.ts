export function isHigherVersion(v1: string | null, v2: string | null): boolean {
  if (v1 == null || v2 == null) return false;
  const v1s = v1.split(".");
  const v2s = v2.split(".");
  if (v1s.length !== v2s.length) {
    throw Error("Comparing incompatible versions: " + v1 + ", " + v2)
  }
  for (var i = 0; i < v1s.length; i++) {
    const one = v1s[i];
    const two = v2s[i];
    let n1 = Number(one);
    let n2 = Number(two);
    if (n1 > n2) {
      return true;
    } else if (n1 < n2) {
      return false; // Don't check more minor versions
    }
  }
  return false;
}
