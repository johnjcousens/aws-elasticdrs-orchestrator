import { createTheme } from '@mui/material/styles';

/**
 * AWS-Branded Material-UI Theme
 * 
 * Custom theme configuration with AWS brand colors and design standards.
 * Based on AWS Style Dictionary and AWS Design System guidelines.
 */

// AWS Brand Colors
const AWS_COLORS = {
  // Primary AWS Orange
  orange: '#FF9900',
  orangeDark: '#EC7211',
  orangeLight: '#FFB84D',
  
  // AWS Squid Ink (Dark Blue)
  squidInk: '#232F3E',
  squidInkLight: '#37475A',
  squidInkDark: '#16191F',
  
  // Supporting Colors
  blue: '#0073BB',
  blueDark: '#005A94',
  blueLight: '#00A8E1',
  
  // Status Colors
  success: '#1D8102',
  warning: '#F89406',
  error: '#D13212',
  info: '#0073BB',
  
  // Neutral Colors
  white: '#FFFFFF',
  grey50: '#FAFAFA',
  grey100: '#F5F5F5',
  grey200: '#EEEEEE',
  grey300: '#E0E0E0',
  grey400: '#BDBDBD',
  grey500: '#9E9E9E',
  grey600: '#757575',
  grey700: '#616161',
  grey800: '#424242',
  grey900: '#212121',
};

// Create Material-UI theme
export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: AWS_COLORS.orange,
      dark: AWS_COLORS.orangeDark,
      light: AWS_COLORS.orangeLight,
      contrastText: AWS_COLORS.white,
    },
    secondary: {
      main: AWS_COLORS.squidInk,
      dark: AWS_COLORS.squidInkDark,
      light: AWS_COLORS.squidInkLight,
      contrastText: AWS_COLORS.white,
    },
    success: {
      main: AWS_COLORS.success,
    },
    warning: {
      main: AWS_COLORS.warning,
    },
    error: {
      main: AWS_COLORS.error,
    },
    info: {
      main: AWS_COLORS.info,
    },
    background: {
      default: AWS_COLORS.grey50,
      paper: AWS_COLORS.white,
    },
    text: {
      primary: AWS_COLORS.squidInk,
      secondary: AWS_COLORS.grey700,
    },
  },
  
  typography: {
    fontFamily: [
      'Amazon Ember',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 700,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.6,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.43,
    },
    button: {
      textTransform: 'none', // AWS doesn't use all-caps buttons
      fontWeight: 600,
    },
  },
  
  shape: {
    borderRadius: 4, // AWS uses subtle rounded corners
  },
  
  components: {
    // Button customization
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          padding: '8px 16px',
          fontSize: '0.875rem',
          fontWeight: 600,
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    
    // AppBar customization
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: AWS_COLORS.squidInk,
        },
      },
    },
    
    // Card customization
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
        },
      },
    },
    
    // Paper customization
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none', // Remove default gradient
        },
      },
    },
    
    // Table customization
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: AWS_COLORS.grey100,
        },
      },
    },
    
    // Chip customization
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 4,
        },
      },
    },
  },
});

// Dark theme variant (optional)
export const darkTheme = createTheme({
  ...theme,
  palette: {
    mode: 'dark',
    primary: {
      main: AWS_COLORS.orange,
      dark: AWS_COLORS.orangeDark,
      light: AWS_COLORS.orangeLight,
      contrastText: AWS_COLORS.squidInk,
    },
    secondary: {
      main: AWS_COLORS.blueLight,
      dark: AWS_COLORS.blue,
      light: AWS_COLORS.blueLight,
      contrastText: AWS_COLORS.squidInk,
    },
    background: {
      default: AWS_COLORS.squidInk,
      paper: AWS_COLORS.squidInkLight,
    },
    text: {
      primary: AWS_COLORS.white,
      secondary: AWS_COLORS.grey300,
    },
  },
});

export default theme;
