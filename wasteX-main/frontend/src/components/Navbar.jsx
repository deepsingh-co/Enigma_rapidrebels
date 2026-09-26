import { Link } from "react-router-dom";
import { Leaf, Menu, LogOut, User as UserIcon, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <header className="fixed top-0 inset-x-0 z-50 transition-all duration-300">
      <div className="absolute inset-0 glass"></div>
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-10">
            <Link to="/" className="flex shrink-0 items-center gap-2 text-xl font-extrabold tracking-tight text-gray-900">
              <div className="bg-accent/10 p-1.5 rounded-lg text-accent mr-1">
                <Leaf className="w-5 h-5" />
              </div>
              WasteX
            </Link>
            <div className="hidden md:flex items-center gap-8">
              <Link to="/" className="text-[13px] font-semibold text-slate-500 hover:text-slate-900 transition-colors uppercase tracking-widest">Home</Link>
              <Link to="/symbiosis" className="text-[13px] font-semibold text-accent hover:text-teal-900 transition-colors flex items-center gap-1.5 uppercase tracking-widest">
                <Sparkles className="w-4 h-4" />
                Symbiosis AI
              </Link>
              <a href="/#marketplace" className="text-[13px] font-semibold text-slate-500 hover:text-slate-900 transition-colors uppercase tracking-widest">Marketplace</a>
              <a href="/#process" className="text-[13px] font-semibold text-slate-500 hover:text-slate-900 transition-colors uppercase tracking-widest">Process</a>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-4">
              <Link to="/create" className="text-sm font-semibold text-white bg-accent px-5 py-2.5 rounded-full hover:bg-teal-700 transition-all shadow-sm hover:shadow hover:-translate-y-0.5">
                List Waste
              </Link>
              
              {user && (
                <Link to="/nearby-buyers" className="text-sm font-semibold text-slate-700 bg-slate-100 px-5 py-2.5 rounded-full hover:bg-slate-200 transition-all">
                  Nearby Buyers
                </Link>
              )}
              
              {user ? (
                <div className="flex items-center gap-4 ml-2 pl-4 border-l border-slate-200">
                  <div className="flex items-center gap-2">
                    {user.photoURL ? (
                      <img src={user.photoURL} alt="Profile" className="w-8 h-8 rounded-full border border-slate-200 shadow-sm" />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center border border-slate-200 shadow-sm">
                        <UserIcon className="w-4 h-4 text-slate-500" />
                      </div>
                    )}
                  </div>
                  <button onClick={logout} className="text-slate-400 hover:text-rose-500 transition-colors p-1" title="Sign out">
                    <LogOut className="w-5 h-5" />
                  </button>
                </div>
              ) : (
                <Link to="/login" className="text-sm font-semibold text-slate-700 bg-slate-100 px-5 py-2.5 rounded-full hover:bg-slate-200 transition-all ml-2">
                  Sign in
                </Link>
              )}
            </div>
            <button className="md:hidden text-slate-600 p-2">
              <Menu className="w-6 h-6" />
            </button>
          </div>
        </div>
      </nav>
    </header>
  );
}

