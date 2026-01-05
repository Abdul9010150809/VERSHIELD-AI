'use client';

import React, { useState, useEffect } from 'react';
import { Card, Title, Text, Metric, Flex, Grid, BarChart, DonutChart, LineChart } from '@tremor/react';

interface FinOpsData {
  current_spend: number;
  requests_today: number;
  avg_cost_per_request: number;
  model_breakdown: Record<string, {
    total_cost: number;
    requests: number;
    tokens: number;
  }>;
  timestamp: string;
}

interface OptimizationSuggestion {
  type: string;
  priority: string;
  model: string;
  suggestion: string;
  estimated_savings: number;
}

export default function FinOpsDashboard() {
  const [data, setData] = useState<FinOpsData | null>(null);
  const [suggestions, setSuggestions] = useState<OptimizationSuggestion[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFinOpsData();
    const interval = setInterval(fetchFinOpsData, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchFinOpsData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/finops/dashboard');
      const finopsData = await response.json();
      setData(finopsData);

      const statsResponse = await fetch('http://localhost:8000/api/finops/stats');
      const stats = await statsResponse.json();
      setSuggestions(stats.optimization_suggestions || []);
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching FinOps data:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8">Loading FinOps Dashboard...</div>;
  }

  if (!data) {
    return <div className="p-8">No data available</div>;
  }

  // Prepare chart data
  const modelBreakdownData = Object.entries(data.model_breakdown).map(([model, stats]) => ({
    model: model,
    cost: Number(stats.total_cost.toFixed(4)),
    requests: stats.requests
  }));

  const costDistribution = Object.entries(data.model_breakdown).map(([model, stats]) => ({
    name: model,
    value: Number(stats.total_cost.toFixed(4))
  }));

  return (
    <div className="p-8 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <Title>FinOps Token Tracking Dashboard</Title>
          <Text>Real-time AI cost monitoring and optimization</Text>
        </div>
        <Text className="text-sm text-gray-500">
          Last updated: {new Date(data.timestamp).toLocaleTimeString()}
        </Text>
      </div>

      {/* Key Metrics */}
      <Grid numItemsMd={3} numItemsLg={4} className="gap-6">
        <Card decoration="top" decorationColor="blue">
          <Text>Today's Spend</Text>
          <Metric>${data.current_spend.toFixed(4)}</Metric>
        </Card>

        <Card decoration="top" decorationColor="green">
          <Text>Total Requests</Text>
          <Metric>{data.requests_today.toLocaleString()}</Metric>
        </Card>

        <Card decoration="top" decorationColor="amber">
          <Text>Avg Cost / Request</Text>
          <Metric>${data.avg_cost_per_request.toFixed(6)}</Metric>
        </Card>

        <Card decoration="top" decorationColor="purple">
          <Text>Active Models</Text>
          <Metric>{Object.keys(data.model_breakdown).length}</Metric>
        </Card>
      </Grid>

      {/* Cost Breakdown Charts */}
      <Grid numItemsLg={2} className="gap-6">
        <Card>
          <Title>Cost by Model</Title>
          <BarChart
            className="mt-6"
            data={modelBreakdownData}
            index="model"
            categories={["cost"]}
            colors={["blue"]}
            valueFormatter={(value) => `$${value.toFixed(4)}`}
            yAxisWidth={48}
          />
        </Card>

        <Card>
          <Title>Cost Distribution</Title>
          <DonutChart
            className="mt-6"
            data={costDistribution}
            category="value"
            index="name"
            valueFormatter={(value) => `$${value.toFixed(4)}`}
            colors={["blue", "cyan", "indigo", "violet", "purple"]}
          />
        </Card>
      </Grid>

      {/* Detailed Model Breakdown */}
      <Card>
        <Title>Model Performance Details</Title>
        <div className="mt-6 overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="py-3 px-4 font-semibold text-sm">Model</th>
                <th className="py-3 px-4 font-semibold text-sm text-right">Total Cost</th>
                <th className="py-3 px-4 font-semibold text-sm text-right">Requests</th>
                <th className="py-3 px-4 font-semibold text-sm text-right">Tokens</th>
                <th className="py-3 px-4 font-semibold text-sm text-right">Avg Cost/Request</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.model_breakdown).map(([model, stats]) => (
                <tr key={model} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 font-medium">{model}</td>
                  <td className="py-3 px-4 text-right">${stats.total_cost.toFixed(4)}</td>
                  <td className="py-3 px-4 text-right">{stats.requests.toLocaleString()}</td>
                  <td className="py-3 px-4 text-right">{stats.tokens.toLocaleString()}</td>
                  <td className="py-3 px-4 text-right">
                    ${(stats.total_cost / stats.requests).toFixed(6)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Optimization Suggestions */}
      {suggestions.length > 0 && (
        <Card>
          <Title>Cost Optimization Suggestions</Title>
          <div className="mt-6 space-y-4">
            {suggestions.map((suggestion, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border-l-4 ${
                  suggestion.priority === 'high'
                    ? 'border-red-500 bg-red-50'
                    : suggestion.priority === 'medium'
                    ? 'border-yellow-500 bg-yellow-50'
                    : 'border-blue-500 bg-blue-50'
                }`}
              >
                <Flex>
                  <div className="flex-1">
                    <Text className="font-semibold">{suggestion.model}</Text>
                    <Text className="mt-1">{suggestion.suggestion}</Text>
                  </div>
                  <div className="text-right">
                    <Text className="text-sm font-semibold text-green-600">
                      Potential Savings
                    </Text>
                    <Metric className="text-green-600">
                      ${suggestion.estimated_savings.toFixed(2)}
                    </Metric>
                  </div>
                </Flex>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
