import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Search, MapPin, Truck, TrendingUp, CheckCircle2, ExternalLink, Sparkles, Building2, Leaf, Send } from "lucide-react";
import axios from "axios";

export default function ListingDetails() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [symbiosisData, setSymbiosisData] = useState(null);
  const [symbiosisLoading, setSymbiosisLoading] = useState(false);
  const [contactModal, setContactModal] = useState({ show: false, buyerName: "", partnerId: null });
  const [message, setMessage] = useState("");
  const [sentRequests, setSentRequests] = useState({});

  useEffect(() => {
    fetchMatch();
  }, [id]);

  const fetchMatch = async () => {
    try {
      const res = await axios.get(`${import.meta.env.VITE_API_URL}/match/${id}`);
      setData(res.data);
      if (res.data?.listing) {
        fetchSymbiosis(res.data.listing);
      }
    } catch (error) {
      console.error("Error fetching match data:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSymbiosis = async (listing) => {
    setSymbiosisLoading(true);
    try {
      const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/symbiosis/analyze`, {
        listing_id: id,
        material: listing.material,
        quantity: listing.quantity,
        location: listing.location,
        form: listing.form,
        condition: listing.condition,
        producer_name: listing.title
      });
      setSymbiosisData(res.data);
    } catch (err) {
      console.warn("Symbiosis auto-analysis failed:", err);
    } finally {
      setSymbiosisLoading(false);
    }
  };

  if (loading) return <div className="flex justify-center py-20"><Search className="w-10 h-10 animate-spin text-accent" /></div>;
  if (!data) return <div className="text-center text-textmuted py-20">Failed to load match data.</div>;

  const { listing, internal_matches, external_leads, market_intelligence } = data;

  const handleConnectClick = (buyerName, partnerId = null) => {
    if (sentRequests[buyerName]) return;
    setContactModal({ show: true, buyerName, partnerId });
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${import.meta.env.VITE_API_URL}/messages`, {
        listing_id: id,
        buyer_name: contactModal.buyerName,
        message: message
      });
      setSentRequests(prev => ({ ...prev, [contactModal.buyerName]: true }));
      setContactModal({ show: false, buyerName: "", partnerId: null });
      setMessage("");
      alert(`Message sent to ${contactModal.buyerName} successfully!`);
    } catch (error) {
      console.error("Error sending message:", error);
      alert("Failed to send message. Please try again.");
    }
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-5xl mx-auto relative pb-20 px-4">
      {/* Contact Modal */}
      {contactModal.show && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4 backdrop-blur-sm">
          <div className="bg-secondary border border-gray-700 p-6 rounded-2xl w-full max-w-md shadow-2xl">
            <h3 className="text-xl font-bold mb-2 text-white">Contact {contactModal.buyerName}</h3>
            <p className="text-sm text-textmuted mb-4">Send a message to initiate the exchange or symbiosis process.</p>
            <form onSubmit={handleSendMessage}>
              <textarea 
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="w-full bg-primary border border-gray-700 rounded-xl p-3 text-white focus:border-accent focus:outline-none min-h-[120px] mb-4 text-sm"
                placeholder="Hi, I'm interested in discussing the waste exchange / feedstock agreement..."
                required
                autoFocus
              ></textarea>
              <div className="flex justify-end gap-3">
                <button 
                  type="button" 
                  onClick={() => setContactModal({ show: false, buyerName: "", partnerId: null })} 
                  className="px-4 py-2 rounded-lg text-textmuted hover:text-white transition-colors text-sm"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="bg-green-600 text-white font-bold py-2 px-6 rounded-lg hover:bg-green-500 transition-colors text-sm"
                >
                  Send Message
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Overview Section */}
      <div className="bg-secondary p-6 rounded-2xl border border-gray-800 flex flex-col md:flex-row justify-between gap-6 shadow-xl">
        <div>
          <h1 className="text-3xl font-bold mb-2 text-white">{listing.title}</h1>
          <p className="text-textmuted flex items-center gap-2 text-sm">
            <MapPin className="w-4 h-4 text-accent" /> {listing.location}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="bg-primary border border-gray-800 px-3 py-1 rounded-full text-xs text-textmain font-mono">Category: {listing.category}</span>
            <span className="bg-primary border border-gray-800 px-3 py-1 rounded-full text-xs text-textmain font-mono">Material: {listing.material}</span>
            <span className="bg-primary border border-gray-800 px-3 py-1 rounded-full text-xs text-textmain font-mono">Condition: {listing.condition}</span>
            <span className="bg-primary border border-gray-800 px-3 py-1 rounded-full text-xs text-textmain font-mono">Form: {listing.form}</span>
          </div>
        </div>
        
        <div className="bg-primary/90 p-5 rounded-xl border border-gray-700 min-w-[220px] text-center flex flex-col justify-center">
          <p className="text-xs text-textmuted mb-1 font-mono uppercase">Expected / Quantity</p>
          <p className="text-2xl font-bold text-accent font-mono">₹{listing.expected_price}/kg</p>
          <p className="text-textmain font-medium text-sm mt-1">{listing.quantity?.toLocaleString()} {listing.quantity_unit} / {listing.frequency}</p>
        </div>
      </div>

      {/* W2RKG Industrial Symbiosis Intelligence Spotlight Banner */}
      <div className="bg-gradient-to-r from-purple-900/30 via-secondary to-accent/10 border border-purple-500/40 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-purple-400 font-mono text-xs uppercase tracking-wider mb-1">
            <Sparkles className="w-4 h-4" /> Industrial Symbiosis Intelligence (W2RKG Engine)
          </div>
          <h3 className="text-xl font-bold text-white">
            Discover Hidden Circular Partners for this {listing.material}
          </h3>
          <p className="text-xs text-textmuted mt-1 max-w-xl">
            Our 33,000+ triple knowledge graph identifies cross-industry transformation pathways (e.g. into secondary construction, polymer, or bio-energy feeds).
          </p>
        </div>
        <Link
          to={`/symbiosis?listingId=${id}&material=${encodeURIComponent(listing.material)}&quantity=${listing.quantity}&location=${encodeURIComponent(listing.location)}`}
          className="bg-accent text-primary font-bold px-5 py-3 rounded-xl hover:bg-orange-500 transition-all flex items-center gap-2 text-sm shadow-lg whitespace-nowrap"
        >
          <Sparkles className="w-4 h-4" />
          Open Full Symbiosis Explorer
        </Link>
      </div>

      {/* W2RKG Discovered Symbiosis Partners Section */}
      {symbiosisData?.potentialPartners && symbiosisData.potentialPartners.length > 0 && (
        <section className="bg-secondary/50 border border-purple-500/30 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-gray-800">
            <div className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-purple-400" />
              <h2 className="text-xl font-bold text-white">Discovered Industrial Symbiosis Partners</h2>
            </div>
            <span className="text-xs font-mono text-purple-400">Knowledge Graph Matched</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {symbiosisData.potentialPartners.slice(0, 4).map((partner, idx) => (
              <div key={idx} className="bg-primary/90 p-5 rounded-xl border border-gray-800 hover:border-purple-500/50 transition-all space-y-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-bold text-white">{partner.industry.company_name}</h3>
                    <p className="text-xs text-purple-400 font-mono">{partner.industry.industry_type} • {partner.distance} km</p>
                  </div>
                  <span className="bg-purple-500/20 text-purple-300 font-mono text-xs px-2.5 py-1 rounded-full font-bold border border-purple-500/40">
                    {partner.matchScore}% Match
                  </span>
                </div>

                <div className="text-xs text-textmuted space-y-1 bg-secondary/60 p-2.5 rounded-lg">
                  <p><strong className="text-white">Transformed Resource:</strong> {partner.transformationPathway.transformed_resource}</p>
                  <p className="line-clamp-1"><strong className="text-white">Process:</strong> {partner.transformationPathway.transforming_process}</p>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <span className="text-[11px] text-green-400 font-mono flex items-center gap-1">
                    <Leaf className="w-3.5 h-3.5" /> {partner.environmentalImpact?.co2_saved_tonnes} t CO₂ saved
                  </span>
                  <button
                    onClick={() => handleConnectClick(partner.industry.company_name, partner.industry.id)}
                    disabled={sentRequests[partner.industry.company_name]}
                    className={`${sentRequests[partner.industry.company_name] ? 'bg-gray-700 text-gray-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-500 text-white'} px-3.5 py-1.5 rounded-lg text-xs font-bold transition-colors`}
                  >
                    {sentRequests[partner.industry.company_name] ? 'Request Sent' : 'Connect'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Col: Matches */}
        <div className="lg:col-span-2 space-y-8">
          <section>
            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2 text-white">
              <CheckCircle2 className="text-green-500" /> Platform Registered Buyers
            </h2>
            {internal_matches && internal_matches.length > 0 ? (
              <div className="space-y-4">
                {internal_matches.map((match, idx) => (
                  <div key={idx} className="bg-secondary p-5 rounded-xl border border-gray-800 hover:border-green-500 transition-colors">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-xl font-bold text-white">{match.name}</h3>
                      <span className="bg-green-500/20 text-green-400 px-2.5 py-1 rounded-full text-xs font-bold border border-green-500/30">
                        {match.compatibility} Match
                      </span>
                    </div>
                    <p className="text-textmuted text-sm mb-4">Distance: {match.distance}</p>
                    
                    <button 
                      onClick={() => handleConnectClick(match.name)} 
                      disabled={sentRequests[match.name]}
                      className={`${sentRequests[match.name] ? 'bg-gray-700 cursor-not-allowed text-gray-400' : 'bg-green-600 hover:bg-green-500 text-white'} px-4 py-2 rounded-lg text-sm font-bold transition-colors`}
                    >
                      {sentRequests[match.name] ? 'Request Sent' : 'Connect with Buyer'}
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-textmuted">No direct internal matches found.</p>
            )}
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2 text-white">
              <Search className="text-accent" /> External Web Discovery
            </h2>
            {external_leads && external_leads.length > 0 ? (
              <div className="space-y-4">
                {external_leads.map((lead, idx) => (
                  <div key={idx} className="bg-primary p-5 rounded-xl border border-gray-800 hover:border-accent transition-colors">
                    <h3 className="text-lg font-bold text-white mb-2">{lead.name}</h3>
                    <p className="text-textmuted text-sm mb-3 line-clamp-2">{lead.snippet}</p>
                    <a href={lead.link} target="_blank" rel="noopener noreferrer" className="text-accent flex items-center gap-1 text-sm font-medium hover:underline">
                      Visit Website <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-textmuted">No external leads found.</p>
            )}
          </section>
        </div>

        {/* Right Col: Intelligence */}
        <div className="space-y-6">
          <div className="bg-secondary p-5 rounded-xl border border-gray-800">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-white">
              <TrendingUp className="text-accent" /> Market Intelligence
            </h3>
            <p className="text-sm text-textmuted mb-2">Observed market range for {listing.material}:</p>
            <p className="text-2xl font-bold text-accent mb-4 font-mono">{market_intelligence?.estimated_price || "N/A"}</p>
            
            {listing.expected_price && market_intelligence?.estimated_price && (
              <p className="text-xs text-textmuted bg-primary p-2.5 rounded-lg border border-gray-800">
                Your expected price (₹{listing.expected_price}) is being compared with web sources.
              </p>
            )}
          </div>

          <div className="bg-secondary p-5 rounded-xl border border-gray-800">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-white">
              <Truck className="text-accent" /> Logistics & Transport Estimate
            </h3>
            <div className="space-y-3 text-sm text-textmuted">
              <div className="flex justify-between">
                <span>Material Gross Value:</span>
                <span className="text-white font-medium font-mono">₹{(listing.quantity * listing.expected_price).toLocaleString()}</span>
              </div>
              <div className="flex justify-between border-b border-gray-800 pb-2">
                <span>Est. Transport (Avg 100km):</span>
                <span className="text-red-400 font-medium font-mono">- ₹3,000</span>
              </div>
              <div className="flex justify-between text-base">
                <span className="text-white font-bold">Est. Net Value:</span>
                <span className="text-green-500 font-bold font-mono">
                  ₹{Math.max(0, (listing.quantity * listing.expected_price) - 3000).toLocaleString()}
                </span>
              </div>
              <p className="text-xs mt-2 italic text-gray-500">*Values are automated estimates.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
