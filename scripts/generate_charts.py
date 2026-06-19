#!/usr/bin/env python3
"""
Generate charts and statistics from JMeter test results.
Produces PNG images for the README report.
"""

import csv
import os
import json
from collections import defaultdict

# Try importing matplotlib, install if not available
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
except ImportError:
    import subprocess
    subprocess.check_call(['pip3', 'install', 'matplotlib'])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, '..', 'results')
IMAGES_DIR = os.path.join(RESULTS_DIR, 'images')

os.makedirs(IMAGES_DIR, exist_ok=True)

# Color palette
COLORS = {
    'primary': '#4F46E5',
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444',
    'info': '#3B82F6',
    'purple': '#8B5CF6',
    'pink': '#EC4899',
    'teal': '#14B8A6',
}

plt.rcParams.update({
    'figure.facecolor': '#1a1a2e',
    'axes.facecolor': '#16213e',
    'axes.edgecolor': '#e94560',
    'axes.labelcolor': '#eaeaea',
    'text.color': '#eaeaea',
    'xtick.color': '#eaeaea',
    'ytick.color': '#eaeaea',
    'grid.color': '#0f3460',
    'grid.alpha': 0.3,
    'font.size': 12,
    'font.family': 'sans-serif',
})


def read_jtl(filepath):
    """Read JTL CSV file and return list of dicts."""
    results = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results


def generate_load_test_charts():
    """Generate charts for Test 01 - Load Test."""
    jtl_path = os.path.join(RESULTS_DIR, '01-load-test', 'results.jtl')
    stats_path = os.path.join(RESULTS_DIR, '01-load-test', 'html-report', 'statistics.json')

    with open(stats_path, 'r') as f:
        stats = json.load(f)

    data = read_jtl(jtl_path)

    # Chart 1: Response Time Distribution
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Test 01: Load Test - GET /posts (10 Users × 5 Loops)', fontsize=16, fontweight='bold', color='#e94560')

    # Response time per request
    labels = [k for k in stats.keys() if k != 'Total']
    avg_times = [stats[k]['meanResTime'] for k in labels]
    min_times = [stats[k]['minResTime'] for k in labels]
    max_times = [stats[k]['maxResTime'] for k in labels]
    p90_times = [stats[k]['pct1ResTime'] for k in labels]

    x = range(len(labels))
    width = 0.2

    bars1 = axes[0].bar([i - 1.5*width for i in x], min_times, width, label='Min', color=COLORS['success'], alpha=0.85)
    bars2 = axes[0].bar([i - 0.5*width for i in x], avg_times, width, label='Avg', color=COLORS['info'], alpha=0.85)
    bars3 = axes[0].bar([i + 0.5*width for i in x], p90_times, width, label='P90', color=COLORS['warning'], alpha=0.85)
    bars4 = axes[0].bar([i + 1.5*width for i in x], max_times, width, label='Max', color=COLORS['danger'], alpha=0.85)

    axes[0].set_xlabel('API Endpoint')
    axes[0].set_ylabel('Response Time (ms)')
    axes[0].set_title('Response Time Comparison')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, fontsize=10)
    axes[0].legend(loc='upper left')
    axes[0].grid(True, axis='y')

    # Response time over time
    timestamps = []
    resp_times = []
    start_time = int(data[0]['timeStamp'])
    for row in data:
        t = (int(row['timeStamp']) - start_time) / 1000.0
        timestamps.append(t)
        resp_times.append(int(row['elapsed']))

    axes[1].scatter(timestamps, resp_times, c=[COLORS['purple'] if row['label'] == 'GET /posts' else COLORS['teal'] for row in data], alpha=0.7, s=30)
    axes[1].set_xlabel('Time (seconds)')
    axes[1].set_ylabel('Response Time (ms)')
    axes[1].set_title('Response Time Over Time')
    axes[1].grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, '01-load-test-response-time.png'), dpi=150, bbox_inches='tight')
    plt.close()

    # Chart 2: Throughput and Summary
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Test 01: Load Test - Performance Summary', fontsize=16, fontweight='bold', color='#e94560')

    # Throughput
    throughputs = [stats[k]['throughput'] for k in labels]
    bars = axes[0].barh(labels, throughputs, color=[COLORS['primary'], COLORS['purple']], alpha=0.85, height=0.5)
    for bar, val in zip(bars, throughputs):
        axes[0].text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2, f'{val:.1f} req/s',
                     ha='left', va='center', fontsize=11, fontweight='bold')
    axes[0].set_xlabel('Throughput (requests/sec)')
    axes[0].set_title('Throughput per Endpoint')
    axes[0].grid(True, axis='x')

    # Pie chart for success rate
    total = stats['Total']
    success = total['sampleCount'] - total['errorCount']
    error = total['errorCount']
    if error == 0:
        axes[1].pie([success], labels=[f'Success\n{success} samples'], colors=[COLORS['success']],
                    autopct='%1.0f%%', startangle=90, textprops={'fontsize': 14, 'fontweight': 'bold'})
    else:
        axes[1].pie([success, error], labels=['Success', 'Error'],
                    colors=[COLORS['success'], COLORS['danger']],
                    autopct='%1.1f%%', startangle=90)
    axes[1].set_title(f'Success Rate (Total: {total["sampleCount"]} samples)')

    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, '01-load-test-summary.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ Generated: 01-load-test charts")


def generate_stress_test_charts():
    """Generate charts for Test 02 - Stress Test."""
    jtl_path = os.path.join(RESULTS_DIR, '02-stress-test', 'results.jtl')
    stats_path = os.path.join(RESULTS_DIR, '02-stress-test', 'html-report', 'statistics.json')

    with open(stats_path, 'r') as f:
        stats = json.load(f)

    data = read_jtl(jtl_path)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Test 02: Stress Test - GET /users (5 → 20 → 50 Users)', fontsize=16, fontweight='bold', color='#e94560')

    # Response time scatter with thread count coloring
    timestamps = []
    resp_times = []
    thread_counts = []
    start_time = int(data[0]['timeStamp'])
    for row in data:
        t = (int(row['timeStamp']) - start_time) / 1000.0
        timestamps.append(t)
        resp_times.append(int(row['elapsed']))
        thread_counts.append(int(row['allThreads']))

    scatter = axes[0].scatter(timestamps, resp_times, c=thread_counts, cmap='YlOrRd', alpha=0.7, s=30, edgecolors='white', linewidth=0.3)
    cbar = plt.colorbar(scatter, ax=axes[0])
    cbar.set_label('Active Threads')
    axes[0].set_xlabel('Time (seconds)')
    axes[0].set_ylabel('Response Time (ms)')
    axes[0].set_title('Response Time vs Active Users')
    axes[0].grid(True)

    # Phase comparison
    phases = {'Phase 1 (5)': [], 'Phase 2 (20)': [], 'Phase 3 (50)': []}
    for row in data:
        tn = row['threadName']
        rt = int(row['elapsed'])
        if 'Phase 1' in tn:
            phases['Phase 1 (5)'].append(rt)
        elif 'Phase 2' in tn:
            phases['Phase 2 (20)'].append(rt)
        elif 'Phase 3' in tn:
            phases['Phase 3 (50)'].append(rt)

    phase_labels = list(phases.keys())
    phase_avgs = [sum(v)/len(v) if v else 0 for v in phases.values()]
    phase_maxes = [max(v) if v else 0 for v in phases.values()]
    phase_mins = [min(v) if v else 0 for v in phases.values()]

    x = range(len(phase_labels))
    width = 0.25
    axes[1].bar([i - width for i in x], phase_mins, width, label='Min', color=COLORS['success'], alpha=0.85)
    axes[1].bar(x, phase_avgs, width, label='Avg', color=COLORS['info'], alpha=0.85)
    axes[1].bar([i + width for i in x], phase_maxes, width, label='Max', color=COLORS['danger'], alpha=0.85)

    axes[1].set_xlabel('Phase (Number of Users)')
    axes[1].set_ylabel('Response Time (ms)')
    axes[1].set_title('Response Time by Phase')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(phase_labels, fontsize=10)
    axes[1].legend()
    axes[1].grid(True, axis='y')

    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, '02-stress-test-analysis.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ Generated: 02-stress-test charts")


def generate_crud_test_charts():
    """Generate charts for Test 03 - CRUD Test."""
    stats_path = os.path.join(RESULTS_DIR, '03-crud-test', 'html-report', 'statistics.json')

    with open(stats_path, 'r') as f:
        stats = json.load(f)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Test 03: CRUD API Test - POST/GET/PUT/DELETE', fontsize=16, fontweight='bold', color='#e94560')

    # CRUD operations comparison
    crud_ops = ['POST /posts - Create', 'GET /posts/1 - Read', 'PUT /posts/1 - Update', 'DELETE /posts/1 - Delete']
    crud_labels = ['POST\n(Create)', 'GET\n(Read)', 'PUT\n(Update)', 'DELETE\n(Delete)']
    crud_colors = [COLORS['success'], COLORS['info'], COLORS['warning'], COLORS['danger']]

    avg_times = []
    p90_times = []
    for op in crud_ops:
        if op in stats:
            avg_times.append(stats[op]['meanResTime'])
            p90_times.append(stats[op]['pct1ResTime'])
        else:
            avg_times.append(0)
            p90_times.append(0)

    x = range(len(crud_labels))
    width = 0.35
    bars1 = axes[0].bar([i - width/2 for i in x], avg_times, width, label='Avg', color=crud_colors, alpha=0.85)
    bars2 = axes[0].bar([i + width/2 for i in x], p90_times, width, label='P90', color=crud_colors, alpha=0.5, edgecolor='white', linewidth=1)

    for bar, val in zip(bars1, avg_times):
        axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, f'{val:.0f}ms',
                     ha='center', va='bottom', fontsize=9, fontweight='bold')

    axes[0].set_xlabel('HTTP Method (CRUD Operation)')
    axes[0].set_ylabel('Response Time (ms)')
    axes[0].set_title('CRUD Response Time Comparison')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(crud_labels, fontsize=10)
    axes[0].legend()
    axes[0].grid(True, axis='y')

    # Throughput comparison
    throughputs = []
    for op in crud_ops:
        if op in stats:
            throughputs.append(stats[op]['throughput'])
        else:
            throughputs.append(0)

    bars = axes[1].barh(crud_labels, throughputs, color=crud_colors, alpha=0.85, height=0.5)
    for bar, val in zip(bars, throughputs):
        axes[1].text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, f'{val:.2f} req/s',
                     ha='left', va='center', fontsize=11, fontweight='bold')
    axes[1].set_xlabel('Throughput (requests/sec)')
    axes[1].set_title('CRUD Throughput Comparison')
    axes[1].grid(True, axis='x')

    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, '03-crud-test-analysis.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ Generated: 03-crud-test charts")


def generate_overall_summary():
    """Generate overall summary chart."""
    fig, ax = plt.subplots(figsize=(14, 7))
    fig.suptitle('📊 JMeter Testing - Overall Summary Report', fontsize=18, fontweight='bold', color='#e94560')

    test_names = ['01 - Load Test\n(10 users × 5 loops)', '02 - Stress Test\n(5→20→50 users)', '03 - CRUD Test\n(5 users × 3 loops)']
    samples = [100, 225, 60]
    errors = [0, 0, 0]
    avg_rts = [65.9, 87.0, 281.6]
    throughputs = [19.8, 22.5, 12.9]

    x = range(len(test_names))
    width = 0.2

    ax.bar([i - 1.5*width for i in x], [s/10 for s in samples], width, label='Samples (÷10)', color=COLORS['info'], alpha=0.85)
    ax.bar([i - 0.5*width for i in x], avg_rts, width, label='Avg RT (ms)', color=COLORS['warning'], alpha=0.85)
    ax.bar([i + 0.5*width for i in x], throughputs, width, label='Throughput (req/s)', color=COLORS['success'], alpha=0.85)
    ax.bar([i + 1.5*width for i in x], errors, width, label='Errors', color=COLORS['danger'], alpha=0.85)

    ax.set_xlabel('Test Scenario')
    ax.set_ylabel('Value')
    ax.set_title('Performance Metrics Comparison Across All Tests')
    ax.set_xticks(x)
    ax.set_xticklabels(test_names, fontsize=11)
    ax.legend(loc='upper right', fontsize=11)
    ax.grid(True, axis='y')

    # Add text annotations
    for i in x:
        ax.annotate(f'✅ 0% Error', xy=(i, max(avg_rts[i], throughputs[i]) + 15),
                     fontsize=10, ha='center', color=COLORS['success'], fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, '00-overall-summary.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ Generated: Overall summary chart")


if __name__ == '__main__':
    print("🚀 Generating JMeter test result charts...\n")
    generate_load_test_charts()
    generate_stress_test_charts()
    generate_crud_test_charts()
    generate_overall_summary()
    print(f"\n✅ All charts saved to: {IMAGES_DIR}")
