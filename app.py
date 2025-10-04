import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import time
import os
from datetime import time as datetime_time

# Import custom modules
from src.route_optimizer import ClassicalOptimizer
from src.quantum_simulator import QuantumOptimizer
from src.map_utils import MapUtils
from src.data_manager import DataManager

# Configure page
st.set_page_config(page_title="Quantum Path Planner for Delivery Vehicles",
                   page_icon="",
                   layout="wide",
                   initial_sidebar_state="expanded")

# Initialize session state
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()
if 'map_utils' not in st.session_state:
    st.session_state.map_utils = MapUtils()
if 'classical_optimizer' not in st.session_state:
    st.session_state.classical_optimizer = ClassicalOptimizer()
if 'quantum_optimizer' not in st.session_state:
    st.session_state.quantum_optimizer = QuantumOptimizer()
if 'optimization_results' not in st.session_state:
    st.session_state.optimization_results = {}


def main():
    # Header
    st.title(" Quantum Path Planner for Delivery Vehicles")
    st.markdown(
        "Compare classical and quantum path planning algorithms with interactive map visualization"
    )

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Select Page", [
        "Route Planning", "Map Visualization", "Performance Dashboard",
        "Data Management"
    ])

    if page == "Route Planning":
        route_planning_page()
    elif page == "Map Visualization":
        map_visualization_page()
    elif page == "Performance Dashboard":
        performance_dashboard_page()
    elif page == "Data Management":
        data_management_page()


def route_planning_page():
    st.header("Route Planning Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Vehicle Configuration")

        # Load vehicles data
        vehicles_df = st.session_state.data_manager.load_vehicles()

        if not vehicles_df.empty:
            selected_vehicle = st.selectbox("Select Vehicle",
                                            vehicles_df['vehicle_id'].tolist())

            vehicle_info = vehicles_df[vehicles_df['vehicle_id'] ==
                                       selected_vehicle].iloc[0]
            st.write(f"**Capacity:** {vehicle_info['capacity']} kg")
            st.write(
                f"**Fuel Efficiency:** {vehicle_info['fuel_efficiency']} km/l")
            st.write(f"**Max Distance:** {vehicle_info['max_distance']} km")
        else:
            st.warning(
                "No vehicles found. Please add vehicles in Data Management.")
            return

    with col2:
        st.subheader("Delivery Configuration")

        # Load delivery locations
        locations_df = st.session_state.data_manager.load_delivery_locations()

        selected_df = pd.DataFrame()  # Initialize selected_df

        if not locations_df.empty:
            selected_locations = st.multiselect(
                "Select Delivery Locations",
                locations_df['location_id'].tolist(),
                default=locations_df['location_id'].tolist()
                [:5]  # Default to first 5
            )

            if selected_locations:
                selected_df = locations_df[locations_df['location_id'].isin(
                    selected_locations)]
                total_weight = selected_df['package_weight'].sum()
                st.write(f"**Total Package Weight:** {total_weight} kg")

                if total_weight > vehicle_info['capacity']:
                    st.error(
                        f"Total weight ({total_weight} kg) exceeds vehicle capacity ({vehicle_info['capacity']} kg)"
                    )
                    return
        else:
            st.warning(
                "No delivery locations found. Please add locations in Data Management."
            )
            return

    # Optimization parameters
    st.subheader("Optimization Parameters")
    col3, col4 = st.columns(2)

    with col3:
        depot_lat = st.number_input("Depot Latitude",
                                    value=40.7589,
                                    step=0.0001,
                                    format="%.4f")
        depot_lon = st.number_input("Depot Longitude",
                                    value=-73.9851,
                                    step=0.0001,
                                    format="%.4f")

    with col4:
        max_time = st.number_input("Max Route Time (hours)",
                                   value=8,
                                   min_value=1,
                                   max_value=24)
        traffic_factor = st.slider("Traffic Factor",
                                   min_value=0.5,
                                   max_value=2.0,
                                   value=1.0,
                                   step=0.1)

    # Optimization buttons
    st.subheader("Run Optimization")
    col5, col6 = st.columns(2)

    with col5:
        if st.button("🔄 Run Classical Optimization", type="primary"):
            with st.spinner("Running classical optimization..."):
                start_time = time.time()

                # Prepare data for optimization
                if selected_df is not None and not selected_df.empty:
                    depot = (depot_lat, depot_lon)
                    delivery_coords = [(row['latitude'], row['longitude'])
                                       for _, row in selected_df.iterrows()]
                else:
                    return

                # Run classical optimization
                classical_result = st.session_state.classical_optimizer.optimize_route(
                    depot, delivery_coords, vehicle_info, max_time,
                    traffic_factor)

                classical_result['computation_time'] = time.time() - start_time
                st.session_state.optimization_results[
                    'classical'] = classical_result

                st.success(
                    f"Classical optimization completed in {classical_result['computation_time']:.2f} seconds"
                )
                st.write(
                    f"**Total Distance:** {classical_result['total_distance']:.2f} km"
                )
                st.write(
                    f"**Total Time:** {classical_result['total_time']:.2f} hours"
                )
                st.write(
                    f"**Fuel Cost:** ${classical_result['fuel_cost']:.2f}")

    with col6:
        if st.button("⚛️ Run Quantum Optimization", type="secondary"):
            with st.spinner("Running quantum optimization simulation..."):
                start_time = time.time()

                # Prepare data for optimization
                if selected_df is not None and not selected_df.empty:
                    depot = (depot_lat, depot_lon)
                    delivery_coords = [(row['latitude'], row['longitude'])
                                       for _, row in selected_df.iterrows()]
                else:
                    return

                # Run quantum optimization simulation
                quantum_result = st.session_state.quantum_optimizer.optimize_route(
                    depot, delivery_coords, vehicle_info, max_time,
                    traffic_factor)

                quantum_result['computation_time'] = time.time() - start_time
                st.session_state.optimization_results[
                    'quantum'] = quantum_result

                st.success(
                    f"Quantum optimization completed in {quantum_result['computation_time']:.2f} seconds"
                )
                st.write(
                    f"**Total Distance:** {quantum_result['total_distance']:.2f} km"
                )
                st.write(
                    f"**Total Time:** {quantum_result['total_time']:.2f} hours"
                )
                st.write(f"**Fuel Cost:** ${quantum_result['fuel_cost']:.2f}")

    # Results comparison
    if 'classical' in st.session_state.optimization_results and 'quantum' in st.session_state.optimization_results:
        st.subheader("Quick Comparison")
        classical = st.session_state.optimization_results['classical']
        quantum = st.session_state.optimization_results['quantum']

        comparison_data = {
            'Metric': [
                'Distance (km)', 'Time (hours)', 'Fuel Cost ($)',
                'Computation Time (s)'
            ],
            'Classical': [
                f"{classical['total_distance']:.2f}",
                f"{classical['total_time']:.2f}",
                f"{classical['fuel_cost']:.2f}",
                f"{classical['computation_time']:.2f}"
            ],
            'Quantum': [
                f"{quantum['total_distance']:.2f}",
                f"{quantum['total_time']:.2f}", f"{quantum['fuel_cost']:.2f}",
                f"{quantum['computation_time']:.2f}"
            ]
        }

        comparison_df = pd.DataFrame(comparison_data)
        st.table(comparison_df)


def map_visualization_page():
    st.header("Interactive Map Visualization")

    if not st.session_state.optimization_results:
        st.warning(
            "No optimization results found. Please run optimization first in the Route Planning page."
        )
        return

    # Map display options
    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("Display Options")
        show_classical = st.checkbox("Show Classical Route", value=True)
        show_quantum = st.checkbox("Show Quantum Route", value=True)
        map_style = st.selectbox(
            "Map Style",
            ["OpenStreetMap", "CartoDB positron", "CartoDB dark_matter"])

    with col2:
        # Create the map
        if 'classical' in st.session_state.optimization_results:
            classical_result = st.session_state.optimization_results[
                'classical']
            center_lat = float(
                np.mean([
                    coord[0] for coord in classical_result['route_coordinates']
                ]))
            center_lon = float(
                np.mean([
                    coord[1] for coord in classical_result['route_coordinates']
                ]))
        else:
            center_lat, center_lon = 40.7589, -73.9851  # Default to NYC

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles=map_style if map_style == "OpenStreetMap" else None)

        if map_style != "OpenStreetMap":
            folium.TileLayer(map_style).add_to(m)

        # Add routes to map
        if show_classical and 'classical' in st.session_state.optimization_results:
            classical_result = st.session_state.optimization_results[
                'classical']

            # Add classical route
            folium.PolyLine(classical_result['route_coordinates'],
                            color='blue',
                            weight=4,
                            opacity=0.8,
                            popup="Classical Route").add_to(m)

            # Add markers for classical route
            for i, coord in enumerate(classical_result['route_coordinates']):
                if i == 0:  # Depot
                    folium.Marker(coord,
                                  popup="Depot (Start/End)",
                                  icon=folium.Icon(color='green',
                                                   icon='home')).add_to(m)
                else:
                    folium.Marker(coord,
                                  popup=f"Delivery {i}",
                                  icon=folium.Icon(color='blue',
                                                   icon='box')).add_to(m)

        if show_quantum and 'quantum' in st.session_state.optimization_results:
            quantum_result = st.session_state.optimization_results['quantum']

            # Add quantum route
            folium.PolyLine(quantum_result['route_coordinates'],
                            color='red',
                            weight=4,
                            opacity=0.8,
                            popup="Quantum Route",
                            dash_array='10, 5').add_to(m)

            # Add markers for quantum route (offset slightly to avoid overlap)
            for i, coord in enumerate(quantum_result['route_coordinates']):
                if i == 0:  # Depot
                    folium.Marker([coord[0] + 0.001, coord[1] + 0.001],
                                  popup="Depot (Quantum)",
                                  icon=folium.Icon(color='darkgreen',
                                                   icon='home')).add_to(m)
                else:
                    folium.Marker([coord[0] + 0.001, coord[1] + 0.001],
                                  popup=f"Delivery {i} (Quantum)",
                                  icon=folium.Icon(color='red',
                                                   icon='box')).add_to(m)

        # Display map
        map_data = st_folium(m, width=700, height=500)

    # Route details
    if st.session_state.optimization_results:
        st.subheader("Route Details")

        tab1, tab2 = st.tabs(["Classical Route", "Quantum Route"])

        with tab1:
            if 'classical' in st.session_state.optimization_results:
                classical_result = st.session_state.optimization_results[
                    'classical']
                st.write(
                    f"**Route Order:** {' → '.join(map(str, classical_result['route_order']))}"
                )
                st.write(
                    f"**Total Distance:** {classical_result['total_distance']:.2f} km"
                )
                st.write(
                    f"**Estimated Time:** {classical_result['total_time']:.2f} hours"
                )
                st.write(
                    f"**Fuel Cost:** ${classical_result['fuel_cost']:.2f}")
            else:
                st.info("Classical optimization results not available")

        with tab2:
            if 'quantum' in st.session_state.optimization_results:
                quantum_result = st.session_state.optimization_results[
                    'quantum']
                st.write(
                    f"**Route Order:** {' → '.join(map(str, quantum_result['route_order']))}"
                )
                st.write(
                    f"**Total Distance:** {quantum_result['total_distance']:.2f} km"
                )
                st.write(
                    f"**Estimated Time:** {quantum_result['total_time']:.2f} hours"
                )
                st.write(f"**Fuel Cost:** ${quantum_result['fuel_cost']:.2f}")
                st.info(
                    "⚛️ This route was optimized using quantum algorithms (QAOA simulation)"
                )
            else:
                st.info("Quantum optimization results not available")


def performance_dashboard_page():
    st.header("Performance Dashboard")

    if not st.session_state.optimization_results:
        st.warning(
            "No optimization results found. Please run optimization first in the Route Planning page."
        )
        return

    if len(st.session_state.optimization_results) < 2:
        st.warning(
            "Please run both classical and quantum optimization to see comparisons."
        )
        return

    classical = st.session_state.optimization_results['classical']
    quantum = st.session_state.optimization_results['quantum']

    # Key metrics comparison
    st.subheader("Key Metrics Comparison")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        distance_improvement = (
            (classical['total_distance'] - quantum['total_distance']) /
            classical['total_distance']) * 100
        st.metric(
            "Distance Improvement",
            f"{distance_improvement:+.1f}%",
            delta=
            f"{quantum['total_distance'] - classical['total_distance']:.1f} km"
        )

    with col2:
        time_improvement = ((classical['total_time'] - quantum['total_time']) /
                            classical['total_time']) * 100
        st.metric(
            "Time Improvement",
            f"{time_improvement:+.1f}%",
            delta=f"{quantum['total_time'] - classical['total_time']:.1f} hrs")

    with col3:
        cost_improvement = ((classical['fuel_cost'] - quantum['fuel_cost']) /
                            classical['fuel_cost']) * 100
        st.metric(
            "Cost Improvement",
            f"{cost_improvement:+.1f}%",
            delta=f"${quantum['fuel_cost'] - classical['fuel_cost']:+.2f}")

    with col4:
        computation_ratio = quantum['computation_time'] / classical[
            'computation_time']
        st.metric(
            "Computation Speed",
            f"{computation_ratio:.1f}x",
            delta=
            f"{quantum['computation_time'] - classical['computation_time']:+.2f}s"
        )

    # Charts
    st.subheader("Detailed Comparison Charts")

    col1, col2 = st.columns(2)

    with col1:
        # Distance and time comparison
        metrics_data = pd.DataFrame({
            'Algorithm': ['Classical', 'Quantum'],
            'Distance (km)':
            [classical['total_distance'], quantum['total_distance']],
            'Time (hours)': [classical['total_time'], quantum['total_time']],
            'Fuel Cost ($)': [classical['fuel_cost'], quantum['fuel_cost']]
        })

        fig1 = px.bar(metrics_data.melt(id_vars=['Algorithm'],
                                        var_name='Metric',
                                        value_name='Value'),
                      x='Metric',
                      y='Value',
                      color='Algorithm',
                      barmode='group',
                      title="Performance Metrics Comparison",
                      color_discrete_map={
                          'Classical': '#1f77b4',
                          'Quantum': '#ff7f0e'
                      })
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # Computation time comparison
        computation_data = pd.DataFrame({
            'Algorithm': ['Classical', 'Quantum'],
            'Computation Time (s)':
            [classical['computation_time'], quantum['computation_time']]
        })

        fig2 = px.bar(computation_data,
                      x='Algorithm',
                      y='Computation Time (s)',
                      title="Computation Time Comparison",
                      color='Algorithm',
                      color_discrete_map={
                          'Classical': '#1f77b4',
                          'Quantum': '#ff7f0e'
                      })
        st.plotly_chart(fig2, use_container_width=True)

    # Efficiency analysis
    st.subheader("Efficiency Analysis")

    efficiency_data = {
        'Metric': [
            'Distance Efficiency', 'Time Efficiency', 'Cost Efficiency',
            'Computation Efficiency'
        ],
        'Classical Score': [100, 100, 100, 100],  # Baseline
        'Quantum Score': [
            100 - distance_improvement, 100 - time_improvement,
            100 - cost_improvement,
            100 / computation_ratio if computation_ratio > 0 else 100
        ]
    }

    efficiency_df = pd.DataFrame(efficiency_data)

    fig3 = go.Figure()

    fig3.add_trace(
        go.Scatterpolar(r=efficiency_df['Classical Score'],
                        theta=efficiency_df['Metric'],
                        fill='toself',
                        name='Classical',
                        line_color='blue'))

    fig3.add_trace(
        go.Scatterpolar(r=efficiency_df['Quantum Score'],
                        theta=efficiency_df['Metric'],
                        fill='toself',
                        name='Quantum',
                        line_color='red'))

    fig3.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 120])),
        showlegend=True,
        title="Algorithm Efficiency Radar Chart")

    st.plotly_chart(fig3, use_container_width=True)

    # Route statistics table
    st.subheader("Detailed Statistics")

    stats_data = {
        'Statistic': [
            'Total Distance (km)', 'Total Time (hours)', 'Fuel Cost ($)',
            'Number of Stops', 'Average Distance per Stop (km)',
            'Computation Time (seconds)', 'Route Efficiency Score'
        ],
        'Classical': [
            f"{classical['total_distance']:.2f}",
            f"{classical['total_time']:.2f}", f"{classical['fuel_cost']:.2f}",
            len(classical['route_order']) - 1,
            f"{classical['total_distance'] / max(1, len(classical['route_order']) - 1):.2f}",
            f"{classical['computation_time']:.3f}",
            f"{100 - (classical['total_distance'] / 10 + classical['total_time']):.1f}"
        ],
        'Quantum': [
            f"{quantum['total_distance']:.2f}", f"{quantum['total_time']:.2f}",
            f"{quantum['fuel_cost']:.2f}",
            len(quantum['route_order']) - 1,
            f"{quantum['total_distance'] / max(1, len(quantum['route_order']) - 1):.2f}",
            f"{quantum['computation_time']:.3f}",
            f"{100 - (quantum['total_distance'] / 10 + quantum['total_time']):.1f}"
        ]
    }

    stats_df = pd.DataFrame(stats_data)
    st.table(stats_df)


def data_management_page():
    st.header("Data Management")

    tab1, tab2 = st.tabs(["Vehicles", "Delivery Locations"])

    with tab1:
        st.subheader("Vehicle Management")

        # Display current vehicles
        vehicles_df = st.session_state.data_manager.load_vehicles()

        if not vehicles_df.empty:
            st.write("**Current Vehicles:**")
            st.dataframe(vehicles_df)
        else:
            st.info("No vehicles found. Add your first vehicle below.")

        # Add new vehicle
        with st.expander("Add New Vehicle"):
            col1, col2 = st.columns(2)

            with col1:
                vehicle_id = st.text_input("Vehicle ID",
                                           placeholder="e.g., TRUCK001")
                capacity = st.number_input("Capacity (kg)",
                                           min_value=1,
                                           value=1000)
                fuel_efficiency = st.number_input("Fuel Efficiency (km/l)",
                                                  min_value=0.1,
                                                  value=8.0,
                                                  step=0.1)

            with col2:
                max_distance = st.number_input("Max Distance (km)",
                                               min_value=1,
                                               value=200)
                vehicle_type = st.selectbox(
                    "Vehicle Type", ["Truck", "Van", "Motorcycle", "Bicycle"])
                fuel_cost_per_liter = st.number_input(
                    "Fuel Cost per Liter ($)",
                    min_value=0.1,
                    value=1.5,
                    step=0.1)

            if st.button("Add Vehicle"):
                if vehicle_id and vehicle_id not in vehicles_df[
                        'vehicle_id'].values:
                    new_vehicle = {
                        'vehicle_id': vehicle_id,
                        'capacity': capacity,
                        'fuel_efficiency': fuel_efficiency,
                        'max_distance': max_distance,
                        'vehicle_type': vehicle_type,
                        'fuel_cost_per_liter': fuel_cost_per_liter
                    }
                    st.session_state.data_manager.add_vehicle(new_vehicle)
                    st.success("Vehicle added successfully!")
                    st.rerun()
                else:
                    st.error("Please provide a unique vehicle ID.")

        # Delete vehicle
        if not vehicles_df.empty:
            with st.expander("Delete Vehicle"):
                vehicle_to_delete = st.selectbox(
                    "Select Vehicle to Delete",
                    vehicles_df['vehicle_id'].tolist())
                if st.button("Delete Vehicle", type="secondary"):
                    st.session_state.data_manager.delete_vehicle(
                        vehicle_to_delete)
                    st.success("Vehicle deleted successfully!")
                    st.rerun()

    with tab2:
        st.subheader("Delivery Location Management")

        # Display current locations
        locations_df = st.session_state.data_manager.load_delivery_locations()

        if not locations_df.empty:
            st.write("**Current Delivery Locations:**")
            st.dataframe(locations_df)
        else:
            st.info(
                "No delivery locations found. Add your first location below.")

        # Add new location
        with st.expander("Add New Delivery Location"):
            col1, col2 = st.columns(2)

            with col1:
                location_id = st.text_input("Location ID",
                                            placeholder="e.g., LOC001")
                address = st.text_area("Address",
                                       placeholder="123 Main St, City, State")
                latitude = st.number_input("Latitude",
                                           value=40.7589,
                                           step=0.0001,
                                           format="%.4f")
                longitude = st.number_input("Longitude",
                                            value=-73.9851,
                                            step=0.0001,
                                            format="%.4f")

            with col2:
                package_weight = st.number_input("Package Weight (kg)",
                                                 min_value=0.1,
                                                 value=10.0,
                                                 step=0.1)
                delivery_window_start = st.time_input("Delivery Window Start",
                                                      value=datetime_time(
                                                          9, 0))
                delivery_window_end = st.time_input("Delivery Window End",
                                                    value=datetime_time(17, 0))
                priority = st.selectbox("Priority", ["Low", "Medium", "High"])

            if st.button("Add Location"):
                if location_id and location_id not in locations_df[
                        'location_id'].values:
                    new_location = {
                        'location_id': location_id,
                        'address': address,
                        'latitude': latitude,
                        'longitude': longitude,
                        'package_weight': package_weight,
                        'delivery_window_start': str(delivery_window_start),
                        'delivery_window_end': str(delivery_window_end),
                        'priority': priority
                    }
                    st.session_state.data_manager.add_delivery_location(
                        new_location)
                    st.success("Delivery location added successfully!")
                    st.rerun()
                else:
                    st.error("Please provide a unique location ID.")

        # Delete location
        if not locations_df.empty:
            with st.expander("Delete Delivery Location"):
                location_to_delete = st.selectbox(
                    "Select Location to Delete",
                    locations_df['location_id'].tolist())
                if st.button("Delete Location", type="secondary"):
                    st.session_state.data_manager.delete_delivery_location(
                        location_to_delete)
                    st.success("Location deleted successfully!")
                    st.rerun()


if __name__ == "__main__":
    main()
