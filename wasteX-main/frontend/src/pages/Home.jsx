import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Package, RefreshCw, Box, Recycle, Leaf, Search, TrendingUp, ShieldCheck } from "lucide-react";
import axios from "axios";

export default function Home() {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    fetchListings();
  }, []);

  const fetchListings = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${import.meta.env.VITE_API_URL}/listings`);
      setListings(res.data);
    } catch (error) {
      console.error("Error fetching listings:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    if (!searchQuery.trim()) {
      fetchListings();
      return;
    }

    try {
      let semanticListings = [];
      try {
        const resSemantic = await axios.post(`${import.meta.env.VITE_API_URL}/search/semantic`, { query: searchQuery });
        semanticListings = resSemantic.data;
      } catch (err) {
        console.warn("Semantic search failed", err);
      }

      const res = await axios.get(`${import.meta.env.VITE_API_URL}/listings`);
      const allListings = res.data;
      const q = searchQuery.toLowerCase();
      const fuzzyListings = allListings.filter(l => 
        (l.title && l.title.toLowerCase().includes(q)) || 
        (l.material && l.material.toLowerCase().includes(q)) ||
        (l.category && l.category.toLowerCase().includes(q)) ||
        (l.location && l.location.toLowerCase().includes(q))
      );

      const mergedMap = new Map();
      semanticListings.forEach(l => mergedMap.set(l._id, l));
      fuzzyListings.forEach(l => mergedMap.set(l._id, l));

      setListings(Array.from(mergedMap.values()));
    } catch (error) {
      console.error("Search error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#f8fafc] min-h-screen font-sans selection:bg-teal-100 selection:text-teal-900 pt-16">
      <main className="relative overflow-hidden">
        {/* Background Decorative Gradients */}
        <div className="absolute top-0 inset-x-0 h-[600px] bg-gradient-to-b from-teal-50/50 to-transparent -z-10 pointer-events-none"></div>
        <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] rounded-full bg-teal-400/10 blur-[100px] -z-10 pointer-events-none"></div>

        {/* Hero Section */}
        <section className="relative border-b border-slate-200/60 bg-dot-pattern">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24 md:pt-28 md:pb-32">
            <div className="grid items-center gap-16 lg:grid-cols-2">
              <div className="animate-fade-up">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-slate-200 shadow-sm text-sm font-semibold text-slate-700 mb-8 premium-shadow">
                  <span className="flex w-2 h-2 rounded-full bg-accent animate-pulse"></span>
                  India's premium B2B waste network
                </div>
                
                <h1 className="text-5xl md:text-6xl lg:text-[72px] font-extrabold text-slate-900 leading-[1.1] tracking-tight mb-8">
                  Industrial <br className="hidden lg:block"/> 
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-600 to-emerald-500">Circularity.</span>
                </h1>
                
                <p className="text-xl text-slate-500 mb-10 max-w-xl leading-relaxed font-medium">
                  A high-performance marketplace for industrial byproducts. Designed for modern enterprises to turn disposal costs into strategic revenue streams.
                </p>
                
                <div className="flex flex-wrap gap-4 mb-14">
                  <Link to="/create" className="inline-flex items-center justify-center bg-accent hover:bg-teal-700 text-white font-semibold py-4 px-8 rounded-full transition-all premium-shadow hover:-translate-y-1 gap-2 text-lg">
                    List your waste
                    <ArrowRight className="w-5 h-5" />
                  </Link>
                  <a href="#marketplace" className="inline-flex items-center justify-center bg-white border border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold py-4 px-8 rounded-full transition-all shadow-sm text-lg">
                    Browse Marketplace
                  </a>
                </div>

                <div className="flex items-center gap-12 border-t border-slate-200/60 pt-8">
                  <div>
                    <div className="flex items-center gap-2 text-slate-400 font-semibold text-xs tracking-widest uppercase mb-3">
                      <Box className="w-4 h-4 text-accent" />
                      Active Listings
                    </div>
                    <div className="text-4xl font-extrabold text-slate-900 tracking-tight">{listings.length > 0 ? listings.length : '0'}</div>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 text-slate-400 font-semibold text-xs tracking-widest uppercase mb-3">
                      <Recycle className="w-4 h-4 text-emerald-500" />
                      Waste Exchanged
                    </div>
                    <div className="text-4xl font-extrabold text-slate-900 tracking-tight">18.7 T</div>
                  </div>
                </div>
              </div>
              
              <div className="hidden lg:flex justify-center items-center relative animate-fade-in" style={{animationDelay: '0.2s'}}>
                <div className="relative w-full max-w-[520px] aspect-square rounded-[2rem] overflow-hidden premium-shadow border border-white/40">
                  <div className="absolute inset-0 bg-slate-900/10 mix-blend-multiply z-10"></div>
                  <img src="https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?auto=format&fit=crop&q=80&w=1000" alt="Industrial Sustainability" className="object-cover w-full h-full transform hover:scale-105 transition-transform duration-1000" />
                  
                  {/* Floating glass card overlay */}
                  <div className="absolute bottom-8 left-8 right-8 glass rounded-2xl p-6 z-20 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-bold text-slate-800 uppercase tracking-widest mb-1">Impact Generated</p>
                      <p className="text-3xl font-extrabold text-accent">4,200 kg</p>
                    </div>
                    <div className="w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center">
                      <Leaf className="w-6 h-6 text-accent" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Marketplace Section */}
        <section id="marketplace" className="py-24 relative">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-16">
              <div className="max-w-2xl">
                <span className="text-accent font-bold tracking-widest uppercase text-xs mb-3 block">01 / Marketplace</span>
                <h2 className="text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight">Exchange Premium Materials.</h2>
              </div>
              
              <div className="w-full md:w-[400px]">
                <form onSubmit={handleSearch} className="flex items-center bg-white border border-slate-200 rounded-full shadow-sm hover:shadow-md focus-within:ring-2 focus-within:ring-accent/20 focus-within:border-accent overflow-hidden transition-all h-14">
                  <div className="pl-5 text-slate-400">
                    <Search className="w-5 h-5" />
                  </div>
                  <input 
                    type="text" 
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search materials..." 
                    className="w-full bg-transparent text-slate-900 font-medium px-4 py-2 outline-none placeholder:text-slate-400 placeholder:font-normal"
                  />
                  <button type="submit" className="bg-slate-900 text-white px-6 h-full font-semibold hover:bg-slate-800 transition-colors">
                    Search
                  </button>
                </form>
              </div>
            </div>
            
            <div>
              {loading ? (
                <div className="flex justify-center py-20">
                  <RefreshCw className="w-10 h-10 animate-spin text-accent" />
                </div>
              ) : listings.length === 0 ? (
                <div className="bg-white border border-slate-200 rounded-2xl p-16 text-center text-slate-500 premium-shadow">
                  <Package className="w-16 h-16 mx-auto text-slate-300 mb-6" />
                  <p className="text-xl font-bold text-slate-900 mb-2">No listings found</p>
                  <p className="text-lg">Be the first to create one on the network.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {listings.map((listing, index) => (
                    <div key={listing._id} className="bg-white border border-slate-200 rounded-2xl p-6 flex flex-col group transition-all duration-300 hover:premium-shadow hover:-translate-y-1 hover:border-accent/30 animate-fade-up" style={{animationDelay: `${index * 0.1}s`}}>
                      <div className="flex justify-between items-start mb-6">
                        <span className="text-xs font-bold uppercase tracking-widest text-accent bg-teal-50 px-3 py-1.5 rounded-full">
                          {listing.category || 'Uncategorized'}
                        </span>
                        <span className="text-xl font-extrabold text-slate-900">
                          ₹{listing.expected_price}<span className="text-sm font-semibold text-slate-400">/kg</span>
                        </span>
                      </div>
                      <h3 className="text-2xl font-bold text-slate-900 mb-4 group-hover:text-accent transition-colors leading-tight">{listing.title}</h3>
                      
                      <div className="mt-auto">
                        <div className="flex items-center gap-4 bg-slate-50 rounded-xl p-4 mb-6 border border-slate-100">
                          <div className="flex-1">
                            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Quantity</p>
                            <p className="text-sm font-semibold text-slate-900">{listing.quantity} {listing.quantity_unit} <span className="text-slate-400 font-normal">/ {listing.frequency}</span></p>
                          </div>
                          <div className="w-px h-8 bg-slate-200"></div>
                          <div className="flex-1">
                            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Location</p>
                            <p className="text-sm font-semibold text-slate-900 truncate" title={listing.location}>{listing.location}</p>
                          </div>
                        </div>
                        <Link to={`/listing/${listing._id}`} className="inline-flex items-center justify-between w-full text-slate-900 font-semibold group-hover:text-accent transition-colors">
                          View full details
                          <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center group-hover:bg-accent/10 transition-colors">
                            <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                          </div>
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Process Section */}
        <section id="process" className="py-24 bg-white border-y border-slate-200/60 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-1/2 h-full bg-slate-50/50 -skew-x-12 translate-x-32 -z-10"></div>
          
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-3xl mx-auto mb-20">
              <span className="text-emerald-500 font-bold tracking-widest uppercase text-xs mb-3 block">02 / Architecture</span>
              <h2 className="text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight mb-6">Built for Scale.</h2>
              <p className="text-slate-500 text-xl font-medium">A highly optimized three-step pipeline to monetize industrial waste with enterprise-grade reliability.</p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-12 relative">
              <div className="hidden md:block absolute top-10 left-[18%] right-[18%] h-0.5 bg-gradient-to-r from-transparent via-slate-200 to-transparent"></div>
              
              <div className="relative text-center group">
                <div className="w-20 h-20 mx-auto bg-white border border-slate-200 rounded-2xl flex items-center justify-center premium-shadow mb-8 relative z-10 transition-transform group-hover:-translate-y-2 group-hover:border-accent">
                  <Box className="w-8 h-8 text-slate-900 group-hover:text-accent transition-colors" />
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4">1. Catalog Assets</h3>
                <p className="text-slate-500 font-medium leading-relaxed">Enterprises securely log surplus materials into our structured database with exact specifications.</p>
              </div>
              
              <div className="relative text-center group">
                <div className="w-20 h-20 mx-auto bg-white border border-slate-200 rounded-2xl flex items-center justify-center premium-shadow mb-8 relative z-10 transition-transform group-hover:-translate-y-2 group-hover:border-accent">
                  <RefreshCw className="w-8 h-8 text-slate-900 group-hover:text-accent transition-colors" />
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4">2. Algorithmic Match</h3>
                <p className="text-slate-500 font-medium leading-relaxed">Our routing engine identifies optimal industrial buyers based on geography and material requirements.</p>
              </div>
              
              <div className="relative text-center group">
                <div className="w-20 h-20 mx-auto bg-white border border-slate-200 rounded-2xl flex items-center justify-center premium-shadow mb-8 relative z-10 transition-transform group-hover:-translate-y-2 group-hover:border-emerald-500">
                  <ShieldCheck className="w-8 h-8 text-slate-900 group-hover:text-emerald-500 transition-colors" />
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4">3. Secure Exchange</h3>
                <p className="text-slate-500 font-medium leading-relaxed">Execute transactions with end-to-end compliance tracking and automated ESG reporting.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Benefits Section */}
        <section id="benefits" className="py-24">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-8 mb-20">
              <div className="max-w-2xl">
                <span className="text-accent font-bold tracking-widest uppercase text-xs mb-3 block">03 / Value Proposition</span>
                <h2 className="text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight">Enterprise Benefits.</h2>
              </div>
              <p className="text-slate-500 text-xl font-medium max-w-md lg:text-right">Measurable impact at every stage of the circular lifecycle.</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="bg-white border border-slate-200 rounded-3xl p-10 flex gap-6 hover:premium-shadow transition-shadow">
                <div className="w-14 h-14 shrink-0 rounded-2xl bg-teal-50 border border-teal-100 flex items-center justify-center">
                  <Leaf className="w-7 h-7 text-accent" />
                </div>
                <div>
                  <h4 className="text-2xl font-bold text-slate-900 mb-3">Zero Waste Certification</h4>
                  <p className="text-slate-500 font-medium leading-relaxed">Generate official documentation required for your corporate ESG compliance and sustainability audits.</p>
                </div>
              </div>
              
              <div className="bg-white border border-slate-200 rounded-3xl p-10 flex gap-6 hover:premium-shadow transition-shadow">
                <div className="w-14 h-14 shrink-0 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center">
                  <TrendingUp className="w-7 h-7 text-emerald-600" />
                </div>
                <div>
                  <h4 className="text-2xl font-bold text-slate-900 mb-3">New Revenue Streams</h4>
                  <p className="text-slate-500 font-medium leading-relaxed">Transform expensive disposal liabilities into profitable assets by selling directly to vetted consumers.</p>
                </div>
              </div>
              
              <div className="bg-white border border-slate-200 rounded-3xl p-10 flex gap-6 hover:premium-shadow transition-shadow">
                <div className="w-14 h-14 shrink-0 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center">
                  <Box className="w-7 h-7 text-blue-600" />
                </div>
                <div>
                  <h4 className="text-2xl font-bold text-slate-900 mb-3">Verified Network</h4>
                  <p className="text-slate-500 font-medium leading-relaxed">Connect exclusively with verified industrial partners, ensuring reliable and professional transactions.</p>
                </div>
              </div>
              
              <div className="bg-white border border-slate-200 rounded-3xl p-10 flex gap-6 hover:premium-shadow transition-shadow">
                <div className="w-14 h-14 shrink-0 rounded-2xl bg-purple-50 border border-purple-100 flex items-center justify-center">
                  <RefreshCw className="w-7 h-7 text-purple-600" />
                </div>
                <div>
                  <h4 className="text-2xl font-bold text-slate-900 mb-3">Carbon Tracking</h4>
                  <p className="text-slate-500 font-medium leading-relaxed">Automatically calculate, monitor, and report the CO2 emissions saved through your circular exchanges.</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
