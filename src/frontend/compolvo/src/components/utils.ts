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

export function evaluatePasswordRules(password: string): boolean | string {
  if (password.length < 10) {
    return "Password must have length of at least 10 characters."
  }
  const testCases = [
    {
      pattern: /[A-Z]/,
      name: "uppercase characters"
    },
    {
      pattern: /[a-z]/,
      name: "lowercase characters"
    },
    {
      pattern: /\d/,
      name: "numbers"
    },
    {
      pattern: /[?!@$%^&*-]/,
      name: "special characters"
    }
  ]
  for (const testCase of testCases) {
    if (!testCase.pattern.test(password)) {
      return "Password must contain " + testCase.name + "."
    }
  }
  return true;

}

export function formatLargeNumber(count: number): string {
  const ordersOfMagnitude = [
    [12, "T"],
    [9, "B"],
    [6, "M"],
    [3, "K"]
  ]
  for (const magnitude of ordersOfMagnitude) {
    const treshold = 10 ** Number(magnitude[0]);
    if (count >= treshold) {
      return (Math.round(count / treshold * 10) / 10).toString() + magnitude[1]
    }
  }
  return count.toString()
}
