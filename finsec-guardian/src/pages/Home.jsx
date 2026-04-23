import React from "react";
import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-blue-900 to-gray-900 text-white">
      <header className="mb-12 text-center">
        <h1 className="text-5xl font-extrabold mb-4 tracking-tight">FinSec Guardian</h1>
        <p className="text-xl max-w-xl mx-auto opacity-80">
          Secure your smart contracts with advanced automated auditing and threat detection.
        </p>
      </header>
      <div className="flex gap-8 mb-12">
        <button
          className="px-8 py-3 rounded bg-blue-600 hover:bg-blue-700 font-semibold text-lg shadow-lg transition"
          onClick={() => navigate("/scanner")}
        >
          Go to Scanner
        </button>
      </div>
      <footer className="opacity-60 text-sm">&copy; {new Date().getFullYear()} FinSec Guardian. All rights reserved.</footer>
    </div>
  );
}
