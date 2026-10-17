# Spec: Unified Dashboard and AI Assistant

## Overview
The current UI separates the "Backtesting Dashboard" and the "Quant AI Assistant" into two distinct pages. This creates friction for users who want to use the AI assistant to help them configure the manual backtesting parameters or vice-versa.

The goal is to merge these into a single, unified interface where:
1. **Manual Backtesting** remains on the sidebar for quick configuration.
2. **The Main Content Area** displays the backtesting results and charts.
3. **The AI Assistant** is integrated into the same page, positioned at the bottom (as a chat interface), allowing users to interact with the system without switching pages.
4. **Optional Chart Rendering**: Users can explicitly request charts via the AI assistant (e.g., "render charts"), and the UI should handle the rendering of these charts in the main area.

## Requirements
- **Functional**:
    - Remove the page navigation (radio buttons) between "Backtesting Dashboard" and "Quant AI Assistant".
    - Integrate the chat interface at the bottom of the main page.
    - Maintain all existing manual backtesting functionality in the sidebar.
    - Allow the AI assistant to trigger the rendering of metrics and charts in the main content area.
    - Ensure the chat history is preserved during the session.
- **Non-Functional**:
    - The UI must remain responsive and clean despite the merged components.
    - Chat interaction should not block the manual backtesting process.

## Technical Design
- **Logic Flow**:
    - The `main()` function in `dashboard.py` will be refactored to remove the `st.sidebar.radio` navigation.
    - A new layout will be implemented:
        - **Sidebar**: `render_sidebar()` (existing logic).
        - **Main Body**: 
            - Top/Middle: `render_hero()`, `render_metrics()`, and `render_charts()` based on either manual run or AI trigger.
            - Bottom: `render_chat()` (refactored from the "Quant AI Assistant" page logic).
- **State Management**:
    - Use `st.session_state` to track whether a backtest was triggered manually or by the AI.
    - Maintain a shared `data` object in session state to allow both the manual runner and the AI assistant to update the displayed charts/metrics.
- **API Changes**: No changes to the backend API are required as the `/chat` and `/backtest` endpoints already provide the necessary data.

## Implementation Plan
1. **UI Refactor**: Remove the navigation radio button from `dashboard.py`.
2. **Layout Integration**:
    - Move the "Quant AI Assistant" logic into a dedicated `render_chat()` function.
    - Update `main()` to render `render_hero()`, the results area, and `render_chat()` sequentially.
3. **State Sharing**:
    - Implement a mechanism to share backtest results between the manual sidebar trigger and the AI chatbot so that `render_metrics` and `render_charts` can be called by either.
4. **Chat-to-Chart Trigger**:
    - Ensure that when the `/chat` endpoint returns `chart_data` and `performance`, the `render_metrics` and `render_charts` functions are invoked in the main area.
5. **Styling**: Adjust CSS to ensure the chat interface at the bottom looks integrated and does not clutter the dashboard.
6. **Verification**: Test manual runs, AI-triggered runs, and the "render charts" request to ensure the UI updates correctly.

## Definition of Done
- [ ] Navigation radio button is removed; only one page exists.
- [ ] Manual backtesting parameters are still in the sidebar and functional.
- [ ] Chat interface is present at the bottom of the page.
- [ ] Running a manual backtest updates the main area charts/metrics.
- [ ] Asking the AI to run a backtest updates the main area charts/metrics.
- [ ] The "render charts" request via AI correctly triggers the visualization logic.
- [ ] UI is visually appealing and does not overlap components.
