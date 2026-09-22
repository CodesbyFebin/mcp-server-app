/**
 * Design Tokens - Shared Visual Design System
 * 
 * Color palettes, typography, spacing, and breakpoints shared
 * across MCPserver.in and app.mcpserver.in.
 */

export const color = {
  navy: "#0A0A2E",
  deepNavy: "#1B1B3B",
  purpleBlue: "#6A5ACD",
  cyan: "#00FFFF",
  gradientStart: "#2563EB",
  gradientEnd: "#1E40AF",
  surface: "#F8FAFC",
  surfaceElevated: "#FFFFFF",
  onSurface: "#1A1A2E",
  onSurfaceVariant: "#FFFFFF",
  error: "#EF4444",
  success: "#22C55E",
  warning: "#F59E0B",
};

export const typography = {
  fontFamily: "Inter, system-ui, sans-serif",
  fontSize: {
    xs: "0.75rem",
    sm: "0.875rem",
    md: "1rem",
    lg: "1.25rem",
    xl: "1.5rem",
    "2xl": "2rem",
    "3xl": "3rem",
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
};

export const spacing = {
  px: "1px",
  zero: "0",
  point5: "0.125rem",
  one: "0.25rem",
  two: "0.5rem",
  three: "0.75rem",
  four: "1rem",
  five: "1.25rem",
  six: "1.5rem",
  eight: "2rem",
  ten: "2.5rem",
  twelve: "3rem",
  sixteen: "4rem",
  twenty: "5rem",
  twentyfour: "6rem",
};

export const breakpoints = {
  xs: "320px",
  sm: "375px",
  md: "390px",
  lg: "414px",
  xl: "768px",
  "2xl": "1024px",
};