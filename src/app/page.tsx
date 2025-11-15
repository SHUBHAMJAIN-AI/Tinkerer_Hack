"use client";

import { useCoAgent, useCopilotAction } from "@copilotkit/react-core";
import { CopilotKitCSSProperties, CopilotSidebar } from "@copilotkit/react-ui";
import { useState } from "react";

// State of the agent, aligned with multi-agent system state
type AgentState = {
  // Existing fields (backward compatible)
  proverbs: string[];
  deals_found: Deal[];
  search_results: SearchResult[];
  price_comparisons: PriceComparison[];

  // Session management
  session_id?: string;
  user_preferences?: Record<string, any>;

  // Task tracking
  current_task?: string;
  task_history?: string[];

  // Multi-agent intermediate results
  raw_search_results?: Deal[];
  verified_results?: Deal[];
  ranked_results?: Deal[];
  final_answer?: string;

  // Agent coordination
  agent_status?: Record<string, string>;
  current_agent?: string;
  agent_errors?: Array<{agent: string; error: string; task?: string}>;

  // Caching metadata
  cache_hit?: boolean;
  cached_queries?: Record<string, any>;

  // Verification metadata
  verification_scores?: Record<string, number>;
  filtered_count?: number;
  verification_summary?: string;

  // Reranking metadata
  reranking_confidence?: number;
  reranking_factors?: Record<string, number>;
  reranking_summary?: string;
}

type Deal = {
  title: string;
  price: string;
  originalPrice?: string;
  discount?: string;
  url: string;
  store: string;
  rating?: number;
  image?: string;
  score?: number;  // Added for verification/ranking scores
  verified?: boolean;  // Added to track verification status
}

type SearchResult = {
  title: string;
  url: string;
  content: string;
  score: number;
}

type PriceComparison = {
  productName: string;
  prices: { store: string; price: string; url: string }[];
}

export default function DealFinderPage() {
  const [themeColor, setThemeColor] = useState("#2563eb"); // Blue theme for shopping

  // 🪁 Frontend Actions: https://docs.copilotkit.ai/guides/frontend-actions
  useCopilotAction({
    name: "setThemeColor",
    parameters: [{
      name: "themeColor",
      description: "The theme color to set. Make sure to pick nice colors for shopping experience.",
      required: true, 
    }],
    handler({ themeColor }: { themeColor: string }) {
      setThemeColor(themeColor);
    },
  });

  return (
    <main style={{ "--copilot-kit-primary-color": themeColor } as CopilotKitCSSProperties}>
      <DealFinderContent themeColor={themeColor} />
      <CopilotSidebar
        clickOutsideToClose={false}
        defaultOpen={true}
        labels={{
          title: "DealFinder AI Assistant",
          initial: "🛒 Welcome to DealFinder AI! I'm your intelligent shopping assistant specializing in finding the best deals and comparing prices.\n\n**Try asking me:**\n- \"Find deals on iPhone 15\"\n- \"Compare prices for MacBook Air\"\n- \"Search for gaming laptops under $1000\"\n- \"Extract product details from this Amazon link\"\n- \"Set the theme to orange\"\n\nI can search across major retailers like Amazon, eBay, Walmart, Target, Best Buy, and Costco to find you the best prices!"
        }}
      />
    </main>
  );
}

function DealFinderContent({ themeColor }: { themeColor: string }) {
  // 🪁 Shared State: https://docs.copilotkit.ai/coagents/shared-state
  // Agent name matches AGENT_TYPE environment variable (defaults to multi_agent)
  const agentName = process.env.NEXT_PUBLIC_AGENT_TYPE || "multi_agent";

  const { state, setState } = useCoAgent<AgentState>({
    name: agentName,
    initialState: {
      proverbs: [
        "The best deal is the one that saves you money and time.",
      ],
      deals_found: [],
      search_results: [],
      price_comparisons: [],
    },
  })

  // 🪁 Frontend Actions for deal finding
  useCopilotAction({
    name: "addDeal",
    parameters: [{
      name: "deal",
      description: "A deal object with title, price, url, store, and other details",
      required: true,
    }],
    handler: ({ deal }: { deal: Deal }) => {
      setState({
        ...state,
        deals_found: [...(state.deals_found || []), deal],
      });
    },
  });

  useCopilotAction({
    name: "addPriceComparison",
    parameters: [{
      name: "comparison",
      description: "A price comparison with product name and prices from different stores",
      required: true,
    }],
    handler: ({ comparison }: { comparison: PriceComparison }) => {
      setState({
        ...state,
        price_comparisons: [...(state.price_comparisons || []), comparison],
      });
    },
  });

  useCopilotAction({
    name: "addProverb",
    parameters: [{
      name: "proverb",
      description: "A shopping-related proverb or wisdom. Make it witty, short and concise.",
      required: true,
    }],
    handler: ({ proverb }: { proverb: string }) => {
      setState({
        ...state,
        proverbs: [...(state.proverbs || []), proverb],
      });
    },
  });

  // 🪁 Generative UI: Deal Cards
  useCopilotAction({
    name: "show_deal_card",
    description: "Display a deal card with product information and pricing",
    parameters: [
      { name: "title", type: "string", required: true },
      { name: "price", type: "string", required: true },
      { name: "store", type: "string", required: true },
      { name: "url", type: "string", required: true },
      { name: "originalPrice", type: "string", required: false },
      { name: "discount", type: "string", required: false },
    ],
    render: ({ args }) => {
      return <DealCard deal={args} themeColor={themeColor} />
    },
  });

  return (
    <div
      style={{ backgroundColor: themeColor }}
      className="min-h-screen w-screen flex justify-center items-center flex-col transition-colors duration-300"
    >
      <div className="bg-white/20 backdrop-blur-md p-8 rounded-2xl shadow-xl max-w-4xl w-full mx-4">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">🛒 DealFinder AI</h1>
          <p className="text-gray-200 italic">Your Smart Shopping Assistant</p>
        </div>
        
        <hr className="border-white/20 my-6" />
        
        {/* Shopping Wisdom Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4">💡 Shopping Wisdom</h2>
          <div className="flex flex-col gap-3">
            {state.proverbs?.map((proverb, index) => (
              <div 
                key={index} 
                className="bg-white/15 p-4 rounded-xl text-white relative group hover:bg-white/20 transition-all"
              >
                <p className="pr-8">{proverb}</p>
                <button 
                  onClick={() => setState({
                    ...state,
                    proverbs: (state.proverbs || []).filter((_, i) => i !== index),
                  })}
                  className="absolute right-3 top-3 opacity-0 group-hover:opacity-100 transition-opacity 
                    bg-red-500 hover:bg-red-600 text-white rounded-full h-6 w-6 flex items-center justify-center"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Deals Found Section */}
        {state.deals_found && state.deals_found.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4">🎯 Deals Found</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {state.deals_found.map((deal, index) => (
                <DealCard key={index} deal={deal} themeColor={themeColor} />
              ))}
            </div>
          </div>
        )}

        {/* Price Comparisons Section */}
        {state.price_comparisons && state.price_comparisons.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4">💰 Price Comparisons</h2>
            <div className="space-y-4">
              {state.price_comparisons.map((comparison, index) => (
                <PriceComparisonCard key={index} comparison={comparison} themeColor={themeColor} />
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {(!state.deals_found || state.deals_found.length === 0) && 
         (!state.price_comparisons || state.price_comparisons.length === 0) && (
          <div className="text-center text-white/80 italic my-8">
            <p className="text-lg mb-4">🔍 No deals found yet.</p>
            <p>Ask me to search for products, compare prices, or find deals!</p>
          </div>
        )}
      </div>
    </div>
  );
}

// Deal Card Component
function DealCard({ deal, themeColor }: { deal: any; themeColor: string }) {
  return (
    <div className="bg-white/15 backdrop-blur-sm p-4 rounded-xl hover:bg-white/20 transition-all">
      <div className="text-white">
        <h3 className="font-bold text-lg mb-2 line-clamp-2">{deal.title}</h3>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl font-bold text-green-300">{deal.price}</span>
          {deal.originalPrice && (
            <span className="text-sm line-through text-gray-300">{deal.originalPrice}</span>
          )}
          {deal.discount && (
            <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">{deal.discount}</span>
          )}
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-200">🏪 {deal.store}</span>
          {deal.rating && (
            <span className="text-sm text-yellow-300">⭐ {deal.rating}</span>
          )}
        </div>
        <a 
          href={deal.url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="mt-3 block bg-blue-500 hover:bg-blue-600 text-white text-center py-2 px-4 rounded-lg transition-colors"
        >
          View Deal
        </a>
      </div>
    </div>
  );
}

// Price Comparison Card Component
function PriceComparisonCard({ comparison, themeColor }: { comparison: PriceComparison; themeColor: string }) {
  const sortedPrices = comparison.prices.sort((a, b) => 
    parseFloat(a.price.replace(/[^0-9.]/g, '')) - parseFloat(b.price.replace(/[^0-9.]/g, ''))
  );

  return (
    <div className="bg-white/15 backdrop-blur-sm p-4 rounded-xl">
      <h3 className="text-white font-bold text-lg mb-3">📊 {comparison.productName}</h3>
      <div className="space-y-2">
        {sortedPrices.map((price, index) => (
          <div key={index} className={`flex justify-between items-center p-2 rounded-lg ${
            index === 0 ? 'bg-green-500/20 border border-green-400' : 'bg-white/10'
          }`}>
            <span className="text-white">{price.store}</span>
            <div className="flex items-center gap-2">
              <span className={`font-bold ${index === 0 ? 'text-green-300' : 'text-white'}`}>
                {price.price}
              </span>
              {index === 0 && <span className="text-green-300 text-xs">💰 Best Price</span>}
              <a 
                href={price.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-300 hover:text-blue-200 text-sm underline"
              >
                View
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
