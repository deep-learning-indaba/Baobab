---
name: Baobab Community Hub
colors:
  surface: '#f8f9fa'
  surface-dim: '#d9dadb'
  surface-bright: '#f8f9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f5'
  surface-container: '#edeeef'
  surface-container-high: '#e7e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#404943'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f2'
  outline: '#707973'
  outline-variant: '#bfc9c1'
  surface-tint: '#2c694e'
  primary: '#0f5238'
  on-primary: '#ffffff'
  primary-container: '#2d6a4f'
  on-primary-container: '#a8e7c5'
  inverse-primary: '#95d4b3'
  secondary: '#3f6653'
  on-secondary: '#ffffff'
  secondary-container: '#beead1'
  on-secondary-container: '#436b58'
  tertiary: '#0132c5'
  on-tertiary: '#ffffff'
  tertiary-container: '#2f4fdd'
  on-tertiary-container: '#d2d7ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#b1f0ce'
  primary-fixed-dim: '#95d4b3'
  on-primary-fixed: '#002114'
  on-primary-fixed-variant: '#0e5138'
  secondary-fixed: '#c1ecd4'
  secondary-fixed-dim: '#a5d0b9'
  on-secondary-fixed: '#002114'
  on-secondary-fixed-variant: '#274e3d'
  tertiary-fixed: '#dee1ff'
  tertiary-fixed-dim: '#bac3ff'
  on-tertiary-fixed: '#001159'
  on-tertiary-fixed-variant: '#0031c4'
  background: '#f8f9fa'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 16px
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
  gutter: 24px
  margin: 32px
  max_width: 1280px
---

## Brand & Style

This design system is built on the intersection of biological resilience and technological advancement. It evokes a sense of organic growth supported by a rigorous, data-driven framework. The personality is authoritative yet welcoming—positioning the platform as a foundational root system for global AI collaboration.

The visual style is **Corporate Modern with subtle Glassmorphism**. It utilizes a "High-Fidelity Hybrid" approach: community-facing surfaces (profiles, discussions, stories) use soft, approachable containers, while analytical surfaces (datasets, admin consoles, model metrics) transition to precise, high-density layouts. The aesthetic prioritizes clarity through generous whitespace, ensuring the interface remains breathable even when displaying complex information.

## Colors

The palette is anchored by **Baobab Green**, a deep, sophisticated emerald representing life and stability. This is paired with **Deep Teal** for high-contrast text and structural elements.

To signal AI innovation, the system employs "Neural Accents": **Electric Blue** for primary actions and interactive states, and **Soft Violet** for highlights, AI-generated content, or experimental features. 

Backgrounds should predominantly use off-white or very light gray to maintain a "fresh" feel, while subtle linear gradients (transitioning from Primary to Secondary) are reserved for hero sections and primary buttons to add depth.

## Typography

This design system uses a dual-font strategy. **Plus Jakarta Sans** is used for headlines to provide a friendly, modern, and slightly rounded personality that feels inclusive. **Inter** is used for all body copy, labels, and data visualizations due to its exceptional legibility at small sizes and its neutral, systematic feel.

For data-heavy views, use `body-sm` with slightly increased line-height to maintain readability. Headlines should utilize tighter letter-spacing to appear more impactful and "designed."

## Layout & Spacing

The system follows a **12-column fixed grid** for desktop, centered within the viewport. Spacing is based on a **4px baseline scale** to ensure mathematical harmony across all components.

- **Community Views:** Use `xl` (48px) padding between major sections and generous margins to emphasize a relaxed, collaborative feel.
- **Data/Admin Views:** Switch to a high-density model using `sm` and `md` spacing to maximize information density without sacrificing clarity.
- **Gaps:** Standardize on 24px gutters for grid layouts to provide clear separation of ideas.

## Elevation & Depth

Depth is established through **Tonal Layers** and **Ambient Shadows**.

1.  **Base Layer:** The primary background (Neutral).
2.  **Surface Layer:** White cards with a subtle 1px border (#E9ECEF) and a very soft, diffused shadow (0px 4px 20px, 4% opacity).
3.  **Overlay Layer:** Modals and dropdowns use a "Glass" effect—semi-transparent white with a 12px backdrop blur—to maintain context of the underlying content.

Avoid heavy, dark shadows. The goal is to make elements appear "light" and floating, rather than physically heavy.

## Shapes

The design system employs a "Contextual Radius" strategy:

- **Interactive Elements (Buttons, Inputs, Chips):** Use `rounded-lg` (1rem) to feel friendly and tactile.
- **Community Containers (Profile cards, Blog posts):** Use `rounded-xl` (1.5rem) to emphasize inclusivity.
- **Data Containers (Tables, Dashboard Widgets):** Scale down to `soft` (0.25rem) or sharp corners to convey precision and technical rigor.

Background motifs should feature organic "branching" lines (representing both the Baobab and neural paths) with a stroke weight of 1px and 10-15% opacity.

## Components

- **Buttons:** Primary buttons use the Baobab Green with white text. Ghost buttons use a 1px teal border.
- **Inputs:** Clean, white fills with a subtle 1px border. On focus, the border transitions to Electric Blue with a soft outer glow.
- **Chips/Tags:** Used for AI categories or skills. Use a low-opacity fill of the accent colors (e.g., 10% Blue fill with Blue text).
- **Cards:** White background, subtle border, and soft elevation. Community cards should feature larger padding (32px), while data cards use 16px.
- **Neural Indicators:** Small, pulsing circular dots used for "Live" initiatives or active computations, utilizing the Soft Violet accent.
- **Progress Bars:** Use a dual-tone gradient to represent "Growth," moving from a light green to the primary Baobab Green.