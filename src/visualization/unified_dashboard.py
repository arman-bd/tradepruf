import http.server
import random
import socketserver
import threading
import webbrowser
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from src.visualization.enhanced_charts import EnhancedBacktestVisualizer


class UnifiedDashboard(EnhancedBacktestVisualizer):
    """Creates a unified dashboard combining all analysis reports."""

    def create_unified_dashboard(
        self,
        portfolio_data: dict[str, pd.Series],
        trades: list[dict],
        equity_series: pd.Series,
        portfolio_returns: dict[str, pd.Series],
        weights: dict[str, float] | None = None,
        format: str = "html",
    ) -> str:
        """Create a unified dashboard with all analyses."""
        # Create individual plots using parent class methods
        equity_fig = self.create_equity_curve(equity_series, trades, format="none")
        drawdown_fig = self.create_drawdown_chart(equity_series, format="none")
        monthly_returns_fig = self.create_monthly_returns_heatmap(
            equity_series, format="none"
        )
        correlation_fig = self.create_correlation_matrix(
            portfolio_returns, format="none"
        )
        pair_comparison_fig = self.create_interactive_pair_comparison(
            portfolio_data, format="none"
        )
        risk_analysis_fig = self.create_portfolio_risk_analysis(
            portfolio_returns, weights, format="none"
        )
        trade_analysis_fig = self.create_trade_analysis(trades, format="none")

        # Adjust figure sizes for dashboard layout
        for fig in [
            equity_fig,
            drawdown_fig,
            monthly_returns_fig,
            correlation_fig,
            pair_comparison_fig,
            risk_analysis_fig,
            trade_analysis_fig,
        ]:
            fig.update_layout(margin={"l": 50, "r": 50, "t": 50, "b": 50})

        # Save the dashboard
        dashboard_path = (
            self.output_dir
            / f"unified_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )

        # Write the HTML file with all plots
        with open(dashboard_path, "w") as f:
            f.write(self._get_dashboard_template())

            # Add all plots as divs
            f.write(
                self._get_plot_variables_script(
                    equity=equity_fig,
                    drawdown=drawdown_fig,
                    monthly=monthly_returns_fig,
                    correlation=correlation_fig,
                    pair=pair_comparison_fig,
                    risk=risk_analysis_fig,
                    trade=trade_analysis_fig,
                )
            )

            # Add plot rendering
            f.write(self._get_plot_rendering_script())

        if format == "interactive":
            self._serve_dashboard(dashboard_path)

        return str(dashboard_path)

    def _serve_dashboard(self, dashboard_path: Path):
        port = random.randint(8000, 8999)
        """Serve the dashboard using a simple HTTP server."""

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(dashboard_path.parent), **kwargs)

        def run_server():
            with socketserver.TCPServer(("", port), Handler) as httpd:
                print(
                    f"\nServing dashboard at http://localhost:{port}/{dashboard_path.name}"
                )
                print("Press Ctrl+C to stop the server.")
                httpd.serve_forever()

        # Start server in a separate thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # Open browser
        webbrowser.open(f"http://localhost:{port}/{dashboard_path.name}")

        try:
            # Keep the main thread running
            server_thread.join()
        except KeyboardInterrupt:
            print("\nShutting down server...")

    def _get_dashboard_template(self) -> str:
        """Get the HTML template for the dashboard."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>TradePruf - Portfolio Analysis Dashboard</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background-color: #f5f5f5; 
                }
                .dashboard-container { 
                    max-width: 1400px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 20px; 
                    border-radius: 8px; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
                }
                .tab-container { 
                    margin-bottom: 20px; 
                }
                .tab-button { 
                    padding: 10px 20px; 
                    margin-right: 5px; 
                    border: none; 
                    background: #f0f0f0; 
                    cursor: pointer; 
                    border-radius: 4px 4px 0 0; 
                }
                .tab-button.active { 
                    background: #007bff; 
                    color: white; 
                }
                .tab-content { 
                    display: none; 
                    padding: 20px; 
                    border: 1px solid #ddd; 
                    border-radius: 0 0 4px 4px; 
                }
                .tab-content.active { 
                    display: block; 
                }
                .chart-container { 
                    margin-bottom: 20px; 
                    min-height: 500px;  /* Increased height */
                }
                h1 { 
                    color: #333; 
                    margin-bottom: 20px; 
                }
                .grid-container { 
                    display: flex;
                    flex-direction: column;
                    gap: 20px;
                    margin-bottom: 20px;
                }
                .chart-wrapper {
                    width: 95%;
                    background: white;
                    border-radius: 4px;
                    padding: 15px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
            </style>
        </head>
        <body>
            <div class="dashboard-container">
                <h1>TradePruf - Portfolio Analysis Dashboard</h1>
                
                <div class="tab-container">
                    <button class="tab-button active" onclick="openTab(event, 'overview')">Portfolio Overview</button>
                    <button class="tab-button" onclick="openTab(event, 'pair-analysis')">Pair Analysis</button>
                    <button class="tab-button" onclick="openTab(event, 'risk-analysis')">Risk Analysis</button>
                    <button class="tab-button" onclick="openTab(event, 'trade-analysis')">Trade Analysis</button>
                </div>

                <div id="overview" class="tab-content active">
                    <div class="grid-container">
                        <div class="chart-wrapper">
                            <div id="equity-curve" class="chart-container"></div>
                        </div>
                        <div class="chart-wrapper">
                            <div id="drawdown-chart" class="chart-container"></div>
                        </div>
                        <div class="chart-wrapper">
                            <div id="monthly-returns" class="chart-container"></div>
                        </div>
                        <div class="chart-wrapper">
                            <div id="correlation-matrix" class="chart-container"></div>
                        </div>
                    </div>
                </div>

                <div id="pair-analysis" class="tab-content">
                    <div class="chart-wrapper">
                        <div id="pair-comparison" class="chart-container"></div>
                    </div>
                </div>

                <div id="risk-analysis" class="tab-content">
                    <div class="chart-wrapper">
                        <div id="risk-dashboard" class="chart-container"></div>
                    </div>
                </div>

                <div id="trade-analysis" class="tab-content">
                    <div class="chart-wrapper">
                        <div id="trade-dashboard" class="chart-container"></div>
                    </div>
                </div>
            </div>

            <script>
                function openTab(evt, tabName) {
                    var i, tabContent, tabButtons;
                    
                    tabContent = document.getElementsByClassName("tab-content");
                    for (i = 0; i < tabContent.length; i++) {
                        tabContent[i].style.display = "none";
                    }
                    
                    tabButtons = document.getElementsByClassName("tab-button");
                    for (i = 0; i < tabButtons.length; i++) {
                        tabButtons[i].className = tabButtons[i].className.replace(" active", "");
                    }
                    
                    document.getElementById(tabName).style.display = "block";
                    evt.currentTarget.className += " active";

                    // Trigger resize event to properly render plots
                    window.dispatchEvent(new Event('resize'));
                }
            </script>
        </body>
        </html>
        """

    def _get_plot_variables_script(self, **figures: go.Figure) -> str:
        """Generate script for plot variables."""
        script = ""
        for name, fig in figures.items():
            script += f"<script>var {name} = {fig.to_json()};</script>\n"
        return script

    def _get_plot_rendering_script(self) -> str:
        """Get script for rendering all plots."""
        return """
            <script>
                function renderPlots() {
                    Plotly.newPlot('equity-curve', equity.data, equity.layout);
                    Plotly.newPlot('drawdown-chart', drawdown.data, drawdown.layout);
                    Plotly.newPlot('monthly-returns', monthly.data, monthly.layout);
                    Plotly.newPlot('correlation-matrix', correlation.data, correlation.layout);
                    Plotly.newPlot('pair-comparison', pair.data, pair.layout);
                    Plotly.newPlot('risk-dashboard', risk.data, risk.layout);
                    Plotly.newPlot('trade-dashboard', trade.data, trade.layout);
                }
                
                // Initial render
                renderPlots();

                // Re-render plots when window is resized
                window.addEventListener('resize', function() {
                    renderPlots();
                });
            </script>
        """
