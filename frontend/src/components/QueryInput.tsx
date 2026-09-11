/**
 * QueryInput Component
 * Allows users to enter natural language queries
 */

import React, { useState } from 'react';

interface QueryInputProps {
  onSubmit: (query: string) => Promise<void>;
  isLoading: boolean;
  error?: string;
}

export const QueryInput: React.FC<QueryInputProps> = ({ onSubmit, isLoading, error }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      await onSubmit(query);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h1 className="text-3xl font-bold text-gray-800 mb-2">ORCA</h1>
      <p className="text-gray-600 mb-6">
        Marine Ecosystem Reasoning with Collaborative Agents
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
            Ask a question about fishing zones
          </label>
          <textarea
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., Find a suitable and safe fishing zone near Kochi tomorrow morning."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={3}
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
            isLoading || !query.trim()
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800'
          }`}
        >
          {isLoading ? 'Reasoning...' : 'Ask ORCA'}
        </button>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}
      </form>

      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          <span className="font-semibold">Example questions:</span>
          <br />• Is it safe to go fishing near Kochi tomorrow morning?
          <br />• Find a suitable fishing zone near Kochi.
        </p>
      </div>
    </div>
  );
};
