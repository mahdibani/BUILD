import { Component } from 'react';
import MaterialIcon from './MaterialIcon';

class SlideErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Slide rendering error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="slide-error-fallback">
          <MaterialIcon name="error_outline" />
          <h3>Unable to render slide</h3>
          <p>An error occurred while rendering this slide. Please try navigating to another slide.</p>
          {this.state.error && (
            <details className="slide-error-details">
              <summary>Error details</summary>
              <pre>{this.state.error.toString()}</pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default SlideErrorBoundary;
