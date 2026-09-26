import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import axios from "axios";
import {
  Sparkles,
  Network,
  Send,
  Building2,
  MapPin,
  Leaf,
  Scale,
  CheckCircle,
  ArrowRight,
  TrendingUp,
  Truck,
  BookOpen,
  Share2,
  RefreshCw,
  Sliders,
  ExternalLink,
  Phone,
  MessageSquare,
  MessageCircle,
  Calendar,
  Layers,
  Wrench,
  AlertTriangle,
  Info,
  Check,
  X
} from "lucide-react";
import SymbiosisNetworkGraph from "../components/SymbiosisNetworkGraph";

export default function SymbiosisDiscovery() {
  const [searchParams] = useSearchParams();
  const listingIdParam = searchParams.get("listingId");

  const [rawTextPrompt, setRawTextPrompt] = useState(
    "We generate 5000 kg of fly ash every month with 8% moisture in Mumbai."
  );
  const [extractingMaterial, setExtractingMaterial] = useState(false);
  const [extractedProfile, setExtractedProfile] = useState(null);

  const [formData, setFormData] = useState({
    material: searchParams.get("material") || "Fly Ash",
    quantity: parseFloat(searchParams.get("quantity")) || 5000,
    quantity_unit: "kg",
    frequency: "monthly",
    form: searchParams.get("form") || "powder",
    condition: searchParams.get("condition") || "dry",
    location: searchParams.get("location") || "Mumbai, Maharashtra",
    producer_name: searchParams.get("producer") || "Tata Thermal Power Plant",
    producer_industry: "Thermal Power & Energy"
  });

  const [selectedIndustryFilter, setSelectedIndustryFilter] = useState("All");
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);

  // Live W2RKG autocompletion
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Detailed Reasoning Modal
  const [reasoningModal, setReasoningModal] = useState({
    show: false,
    partner: null,
    activeTab: "overview" // "overview" | "timing" | "logistics" | "processing" | "environmental"
  });

  // Twilio Direct Contact Modal
  const [twilioModal, setTwilioModal] = useState({
    show: false,
    partner: null,
    channel: "sms",
    recipientPhone: "",
    customMessage: "",
    sending: false,
    receipt: null,
    error: null
  });

  const handleExtractMaterial = async () => {
    if (!rawTextPrompt.trim()) return;
    setExtractingMaterial(true);
    try {
      const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/symbiosis/material-analysis`, {
        description: rawTextPrompt,
        quantity: parseFloat(formData.quantity) || null,
        location: formData.location
      });
      setExtractedProfile(res.data);
      const newForm = {
        ...formData,
        material: res.data.material_name || formData.material,
        quantity: res.data.quantity || formData.quantity,
        frequency: res.data.availability_frequency || formData.frequency,
        form: res.data.physical_properties?.form?.value || formData.form,
        condition: res.data.physical_properties?.condition?.value || formData.condition
      };
      setFormData(newForm);
      await runSymbiosisAnalysis(newForm, res.data);
    } catch (err) {
      console.error("Material analysis error:", err);
    } finally {
      setExtractingMaterial(false);
    }
  };

  const handleMaterialChange = async (e) => {
    const val = e.target.value;
    setFormData((prev) => ({ ...prev, material: val }));
    if (val.length >= 2) {
      try {
        const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/symbiosis/quick-match`, {
          query: val,
          top_k: 5
        });
        setSuggestions(res.data.matched_wastes || []);
        setShowSuggestions(true);
      } catch (err) {}
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const selectSuggestion = (name) => {
    setFormData((prev) => ({ ...prev, material: name }));
    setShowSuggestions(false);
  };

  const runSymbiosisAnalysis = async (customData = null, customProfile = null) => {
    const dataToSubmit = customData || formData;
    setLoading(true);
    setError(null);
    try {
      const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/symbiosis/analyze`, {
        ...dataToSubmit,
        quantity: parseFloat(dataToSubmit.quantity) || 5000,
        raw_description: rawTextPrompt
      });
      setAnalysisResult(res.data);
      if (res.data.material_profile) {
        setExtractedProfile(res.data.material_profile);
      }
    } catch (err) {
      console.error("Symbiosis analysis error:", err);
      setError("Failed to run symbiosis intelligence analysis.");
    } finally {
      setLoading(false);
    }
  };

  const handleApplyPreset = (preset) => {
    setFormData(preset.data);
    setRawTextPrompt(preset.prompt);
    runSymbiosisAnalysis(preset.data);
  };

  const openTwilioModal = (partner, channel = "sms") => {
    const defaultMsg = `WasteX Symbiosis Alert: ${formData.producer_name} has ${formData.quantity.toLocaleString()} kg of ${formData.material} available in ${formData.location}, matching your ${partner.transformationPathway.transformed_resource} demand (Opportunity Score: ${partner.opportunityScore}%).`;
    setTwilioModal({
      show: true,
      partner,
      channel,
      recipientPhone: partner.industry.contact_phone || "+919820011223",
      customMessage: defaultMsg,
      sending: false,
      receipt: null,
      error: null
    });
  };

  const submitTwilioNotification = async (e) => {
    e.preventDefault();
    setTwilioModal((prev) => ({ ...prev, sending: true, error: null }));
    try {
      const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/symbiosis/notify`, {
        channel: twilioModal.channel,
        recipient_phone: twilioModal.recipientPhone,
        partner_name: twilioModal.partner.industry.company_name,
        producer_name: formData.producer_name,
        waste_material: formData.material,
        quantity: formData.quantity,
        custom_message: twilioModal.customMessage,
        notification_type: "connection_request"
      });
      setTwilioModal((prev) => ({ ...prev, sending: false, receipt: res.data, error: null }));
    } catch (err) {
      console.error("Twilio dispatch error:", err);
      const errMsg = err.response?.data?.detail || "Failed to dispatch Twilio notification. Please verify phone number and parameters.";
      setTwilioModal((prev) => ({ ...prev, sending: false, error: errMsg }));
    }
  };

  const filteredPartners = analysisResult?.potentialPartners?.filter((p) => {
    if (selectedIndustryFilter === "All") return true;
    return p.industry.industry_type.toLowerCase().includes(selectedIndustryFilter.toLowerCase());
  }) || [];

  return (
    <div className="bg-primary text-textmain min-h-screen font-sans pb-28">
      {/* ─────────────────────────────────────────────────────────────
          1. REASONING & EVIDENCE BREAKDOWN MODAL ("WHY IS THIS AN OPPORTUNITY?")
      ───────────────────────────────────────────────────────────── */}
      {reasoningModal.show && reasoningModal.partner && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4 backdrop-blur-md animate-fade-in">
          <div className="bg-secondary border border-gray-700 rounded-2xl w-full max-w-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="p-6 border-b border-gray-800 flex justify-between items-start">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono uppercase bg-purple-500/20 text-purple-400 px-2.5 py-0.5 rounded font-bold">
                    Score: {reasoningModal.partner.opportunityScore}%
                  </span>
                  <span className="text-xs text-textmuted font-mono">• {reasoningModal.partner.industry.industry_type}</span>
                </div>
                <h3 className="text-2xl font-bold text-white mt-1">
                  {reasoningModal.partner.industry.company_name}
                </h3>
                <p className="text-xs text-textmuted mt-0.5">
                  Complete 9-Factor Technical Feasibility & Opportunity Evidence Breakdown
                </p>
              </div>
              <button
                onClick={() => setReasoningModal({ show: false, partner: null, activeTab: "overview" })}
                className="text-textmuted hover:text-white p-2 rounded-lg bg-primary border border-gray-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Navigation Tabs */}
            <div className="flex border-b border-gray-800 px-6 bg-primary/60 overflow-x-auto text-xs font-mono uppercase">
              {["overview", "timing", "logistics", "processing", "environmental"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setReasoningModal({ ...reasoningModal, activeTab: tab })}
                  className={`py-3 px-4 border-b-2 font-semibold transition-all whitespace-nowrap ${
                    reasoningModal.activeTab === tab
                      ? "border-accent text-accent bg-accent/5"
                      : "border-transparent text-textmuted hover:text-white"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Modal Body Tab Content */}
            <div className="p-6 overflow-y-auto space-y-6 text-sm">
              {reasoningModal.activeTab === "overview" && (
                <div className="space-y-6">
                  {/* Executive Summary */}
                  <div className="bg-primary p-4 rounded-xl border border-accent/30 text-xs leading-relaxed text-textmain">
                    <strong className="text-accent uppercase font-mono block mb-1">Executive Match Rationale:</strong>
                    {reasoningModal.partner.summary_reasoning}
                  </div>

                  {/* 9-Factor Score Grid */}
                  <div>
                    <h4 className="text-xs font-mono uppercase text-textmuted mb-3 font-semibold">
                      Multi-Factor Assessment Score Matrix (0–100)
                    </h4>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {Object.entries(reasoningModal.partner.factor_breakdown || {}).map(([key, val]) => (
                        <div key={key} className="bg-primary p-3 rounded-xl border border-gray-800">
                          <span className="text-[10px] uppercase font-mono text-textmuted block truncate">
                            {key.replace(/_/g, " ")}
                          </span>
                          <div className="flex items-center justify-between mt-1">
                            <span className="text-lg font-bold font-mono text-accent">{val}%</span>
                            <div className="w-12 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-accent rounded-full"
                                style={{ width: `${Math.min(100, val)}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Evidence Points */}
                  <div>
                    <h4 className="text-xs font-mono uppercase text-accent mb-2 font-semibold">
                      Transparent Evidence Points:
                    </h4>
                    <ul className="space-y-2 text-xs text-textmain/90">
                      {reasoningModal.partner.reasons?.map((r, i) => (
                        <li key={i} className="flex items-start gap-2 bg-primary/40 p-2.5 rounded-lg border border-gray-800/80">
                          <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {reasoningModal.activeTab === "timing" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-primary rounded-xl border border-blue-500/30">
                    <div>
                      <span className="text-xs font-mono text-blue-400 uppercase">Timing Compatibility Status</span>
                      <h4 className="text-lg font-bold text-white mt-0.5">
                        {reasoningModal.partner.timing_analysis?.status}
                      </h4>
                    </div>
                    <span className="text-2xl font-bold font-mono text-blue-400">
                      {reasoningModal.partner.timing_analysis?.timing_score}%
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div className="bg-primary p-4 rounded-xl border border-gray-800 space-y-1">
                      <span className="text-textmuted font-mono uppercase">Producer Availability</span>
                      <p className="text-white font-semibold">{reasoningModal.partner.timing_analysis?.producer_schedule}</p>
                    </div>
                    <div className="bg-primary p-4 rounded-xl border border-gray-800 space-y-1">
                      <span className="text-textmuted font-mono uppercase">Receiver Intake Window</span>
                      <p className="text-white font-semibold">{reasoningModal.partner.timing_analysis?.receiver_schedule}</p>
                    </div>
                  </div>

                  <div className="bg-primary p-4 rounded-xl border border-gray-800 space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-textmuted">Scheduling Overlap:</span>
                      <span className="text-white font-bold">{reasoningModal.partner.timing_analysis?.scheduling_overlap_days} days buffer</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-textmuted">Quantity Overlap:</span>
                      <span className="text-accent font-bold">{reasoningModal.partner.timing_analysis?.quantity_overlap_kg?.toLocaleString()} kg</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-textmuted">Demand Coverage:</span>
                      <span className="text-emerald-400 font-bold">{reasoningModal.partner.timing_analysis?.demand_coverage_percent}%</span>
                    </div>
                    <p className="text-textmuted pt-2 border-t border-gray-800">
                      {reasoningModal.partner.timing_analysis?.explanation}
                    </p>
                  </div>
                </div>
              )}

              {reasoningModal.activeTab === "logistics" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-primary rounded-xl border border-blue-500/30">
                    <div>
                      <span className="text-xs font-mono text-blue-400 uppercase">Logistics Feasibility Status</span>
                      <h4 className="text-lg font-bold text-white mt-0.5">
                        {reasoningModal.partner.logistics_analysis?.feasibility_status}
                      </h4>
                    </div>
                    <span className="text-2xl font-bold font-mono text-blue-400">
                      {reasoningModal.partner.logistics_analysis?.logistics_score}%
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div className="bg-primary p-3 rounded-xl border border-gray-800">
                      <span className="text-textmuted font-mono text-[10px] uppercase">Distance</span>
                      <p className="text-white font-bold text-sm font-mono mt-0.5">{reasoningModal.partner.logistics_analysis?.distance_km} km</p>
                    </div>
                    <div className="bg-primary p-3 rounded-xl border border-gray-800">
                      <span className="text-textmuted font-mono text-[10px] uppercase">Transport Mode</span>
                      <p className="text-white font-bold text-xs truncate mt-0.5">{reasoningModal.partner.logistics_analysis?.transport_mode}</p>
                    </div>
                    <div className="bg-primary p-3 rounded-xl border border-gray-800">
                      <span className="text-textmuted font-mono text-[10px] uppercase">Est. Freight Cost</span>
                      <p className="text-accent font-bold text-sm font-mono mt-0.5">₹{reasoningModal.partner.logistics_analysis?.estimated_transport_cost_inr?.toLocaleString()}</p>
                    </div>
                    <div className="bg-primary p-3 rounded-xl border border-gray-800">
                      <span className="text-textmuted font-mono text-[10px] uppercase">Transit Duration</span>
                      <p className="text-white font-bold text-sm font-mono mt-0.5">{reasoningModal.partner.logistics_analysis?.estimated_transit_hours} hrs</p>
                    </div>
                  </div>

                  {reasoningModal.partner.logistics_analysis?.warnings?.length > 0 && (
                    <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs text-amber-300 space-y-1">
                      <span className="font-bold flex items-center gap-1 font-mono uppercase">
                        <AlertTriangle className="w-3.5 h-3.5" /> Logistics Warnings:
                      </span>
                      {reasoningModal.partner.logistics_analysis.warnings.map((w, i) => (
                        <p key={i}>• {w}</p>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {reasoningModal.activeTab === "processing" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-primary rounded-xl border border-emerald-500/30">
                    <div>
                      <span className="text-xs font-mono text-emerald-400 uppercase">Processing Complexity</span>
                      <h4 className="text-lg font-bold text-white mt-0.5">
                        {reasoningModal.partner.processing_analysis?.processing_complexity} Complexity
                      </h4>
                    </div>
                    <span className="text-2xl font-bold font-mono text-emerald-400">
                      {reasoningModal.partner.processing_analysis?.processing_score}%
                    </span>
                  </div>

                  <div className="bg-primary p-4 rounded-xl border border-gray-800 text-xs space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-textmuted">Receiver Direct Intake:</span>
                      <span className={`font-bold px-2 py-0.5 rounded ${reasoningModal.partner.processing_analysis?.receiver_can_accept_directly ? "bg-green-500/20 text-green-400" : "bg-amber-500/20 text-amber-400"}`}>
                        {reasoningModal.partner.processing_analysis?.receiver_can_accept_directly ? "Direct Plant Intake Feasible" : "Intermediate Preprocessing Required"}
                      </span>
                    </div>

                    <div>
                      <span className="text-textmuted font-mono uppercase block mb-1.5">Required Preprocessing Steps:</span>
                      <ul className="space-y-1 pl-1">
                        {reasoningModal.partner.processing_analysis?.preprocessing_steps?.map((st, i) => (
                          <li key={i} className="flex items-center gap-2 text-white">
                            <Wrench className="w-3.5 h-3.5 text-accent shrink-0" />
                            <span>{st}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <p className="text-textmuted pt-2 border-t border-gray-800">
                      {reasoningModal.partner.processing_analysis?.technical_explanation}
                    </p>
                  </div>
                </div>
              )}

              {reasoningModal.activeTab === "environmental" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-primary rounded-xl border border-green-500/30">
                    <div>
                      <span className="text-xs font-mono text-green-400 uppercase">Net Avoided Carbon</span>
                      <h4 className="text-lg font-bold text-white mt-0.5">
                        {reasoningModal.partner.environmentalImpact?.net_co2_saved_tonnes} tonnes CO₂e
                      </h4>
                    </div>
                    <span className="text-2xl font-bold font-mono text-green-400">
                      {reasoningModal.partner.environmentalImpact?.environmental_score}%
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="bg-primary p-3 rounded-xl border border-gray-800">
                      <span className="text-textmuted font-mono uppercase">Waste Diverted</span>
                      <p className="text-white font-bold text-sm font-mono mt-0.5">{reasoningModal.partner.environmentalImpact?.waste_diverted_tonnes} tonnes</p>
                    </div>
                    <div className="bg-primary p-3 rounded-xl border border-gray-800">
                      <span className="text-textmuted font-mono uppercase">Virgin Material Saved</span>
                      <p className="text-emerald-400 font-bold text-sm font-mono mt-0.5">{reasoningModal.partner.environmentalImpact?.virgin_material_replaced_tonnes} tonnes</p>
                      <span className="text-[10px] text-gray-500 truncate block">({reasoningModal.partner.environmentalImpact?.replaced_virgin_material_name})</span>
                    </div>
                  </div>

                  <div className="bg-primary p-4 rounded-xl border border-gray-800 text-xs space-y-1 text-textmuted">
                    <div className="flex justify-between">
                      <span>Gross Avoided Production CO₂e:</span>
                      <span className="text-white font-mono">{reasoningModal.partner.environmentalImpact?.gross_avoided_emissions_tonnes_co2e} t</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Transportation Freight Emissions:</span>
                      <span className="text-red-400 font-mono">- {reasoningModal.partner.environmentalImpact?.transportation_emissions_tonnes_co2e} t</span>
                    </div>
                    <div className="flex justify-between pt-1 border-t border-gray-800 text-white font-bold">
                      <span>Net Environmental Benefit:</span>
                      <span className="text-green-400 font-mono">{reasoningModal.partner.environmentalImpact?.net_co2_saved_tonnes} tonnes CO₂e</span>
                    </div>
                    <p className="text-[10px] text-gray-500 pt-2 border-t border-gray-800">
                      <strong>LCA Assumption Source:</strong> {reasoningModal.partner.environmentalImpact?.data_source_citation}
                    </p>
                  </div>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-gray-800 bg-primary/80 flex justify-between items-center">
              <button
                onClick={() => setReasoningModal({ show: false, partner: null, activeTab: "overview" })}
                className="px-4 py-2 rounded-xl text-xs text-textmuted hover:text-white"
              >
                Close Breakdown
              </button>
              <button
                onClick={() => {
                  const p = reasoningModal.partner;
                  setReasoningModal({ show: false, partner: null, activeTab: "overview" });
                  openTwilioModal(p, "sms");
                }}
                className="bg-accent text-primary font-bold px-5 py-2.5 rounded-xl hover:bg-orange-500 text-xs flex items-center gap-1.5"
              >
                <Phone className="w-3.5 h-3.5" /> Contact via Twilio
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          2. TWILIO MULTI-CHANNEL CONTACT MODAL (SMS, WHATSAPP, VOICE)
      ───────────────────────────────────────────────────────────── */}
      {twilioModal.show && twilioModal.partner && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4 backdrop-blur-sm animate-fade-in">
          <div className="bg-secondary border border-gray-700 p-6 md:p-8 rounded-2xl w-full max-w-lg shadow-2xl relative">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  <Phone className="w-5 h-5 text-accent" />
                  Twilio Direct Partner Dispatch
                </h3>
                <p className="text-xs text-textmuted mt-0.5">
                  Contact <span className="text-white font-semibold">{twilioModal.partner.industry.company_name}</span> via SMS, WhatsApp, or Automated Voice Call.
                </p>
              </div>
              <button
                onClick={() => setTwilioModal({ show: false, partner: null, channel: "sms", recipientPhone: "", customMessage: "", sending: false, receipt: null })}
                className="text-textmuted hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {twilioModal.receipt ? (
              <div className="space-y-4 my-4 animate-fade-in">
                <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-xl text-center">
                  <CheckCircle className="w-10 h-10 text-green-500 mx-auto mb-2" />
                  <h4 className="text-base font-bold text-white">Twilio {twilioModal.receipt.channel} Dispatched!</h4>
                  <p className="text-xs text-textmuted mt-0.5">SID: {twilioModal.receipt.sid}</p>
                  <span className="inline-block mt-2 text-[10px] font-mono px-2 py-0.5 rounded bg-green-500/20 text-green-400 font-bold uppercase">
                    Status: {twilioModal.receipt.status}
                  </span>
                </div>
                <div className="p-3 bg-primary rounded-xl border border-gray-800 text-xs text-textmuted space-y-1">
                  <div className="flex justify-between"><span>Recipient:</span><span className="text-white font-mono">{twilioModal.receipt.to}</span></div>
                  <div className="flex justify-between"><span>Timestamp:</span><span className="text-white font-mono">{twilioModal.receipt.timestamp}</span></div>
                  {twilioModal.receipt.note && <p className="text-[11px] text-accent pt-1 italic">{twilioModal.receipt.note}</p>}
                </div>
                <button
                  onClick={() => setTwilioModal({ show: false, partner: null, channel: "sms", recipientPhone: "", customMessage: "", sending: false, receipt: null, error: null })}
                  className="w-full py-2.5 bg-secondary border border-gray-700 text-white rounded-xl text-xs font-semibold hover:bg-gray-800"
                >
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={submitTwilioNotification} className="space-y-4 mt-4">
                {twilioModal.error && (
                  <div className="p-3 bg-red-500/15 border border-red-500/40 rounded-xl text-xs text-red-400 flex items-start gap-2 animate-fade-in">
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{twilioModal.error}</span>
                  </div>
                )}
                {/* Channel Selector */}
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-textmuted mb-1.5">
                    Select Twilio Communication Channel:
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { id: "sms", label: "Twilio SMS", icon: MessageSquare },
                      { id: "whatsapp", label: "WhatsApp", icon: MessageCircle },
                      { id: "voice", label: "Voice Call", icon: Phone }
                    ].map((ch) => {
                      const Icon = ch.icon;
                      return (
                        <button
                          key={ch.id}
                          type="button"
                          onClick={() => setTwilioModal({ ...twilioModal, channel: ch.id })}
                          className={`p-2.5 rounded-xl border text-xs font-mono flex flex-col items-center gap-1 transition-all ${
                            twilioModal.channel === ch.id
                              ? "border-accent bg-accent/15 text-accent font-bold shadow-md"
                              : "border-gray-800 bg-primary text-textmuted hover:border-gray-700 hover:text-white"
                          }`}
                        >
                          <Icon className="w-4 h-4" />
                          <span>{ch.label}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Recipient Phone */}
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-textmuted mb-1">
                    Partner Phone Number (E.164 format)
                  </label>
                  <input
                    type="text"
                    required
                    value={twilioModal.recipientPhone}
                    onChange={(e) => setTwilioModal({ ...twilioModal, recipientPhone: e.target.value })}
                    className="w-full bg-primary border border-gray-700 rounded-xl p-2.5 text-sm text-white focus:border-accent focus:outline-none font-mono"
                  />
                </div>

                {/* Message Body */}
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-textmuted mb-1">
                    Notification Payload / Spoken Script
                  </label>
                  <textarea
                    rows="4"
                    required
                    value={twilioModal.customMessage}
                    onChange={(e) => setTwilioModal({ ...twilioModal, customMessage: e.target.value })}
                    className="w-full bg-primary border border-gray-700 rounded-xl p-3 text-xs text-white focus:border-accent focus:outline-none"
                  ></textarea>
                </div>

                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setTwilioModal({ show: false, partner: null, channel: "sms", recipientPhone: "", customMessage: "", sending: false, receipt: null })}
                    className="px-4 py-2 rounded-xl text-xs text-textmuted hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={twilioModal.sending}
                    className="bg-accent text-primary font-bold px-6 py-2.5 rounded-xl hover:bg-orange-500 transition-all flex items-center gap-2 text-xs disabled:opacity-50"
                  >
                    {twilioModal.sending ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" /> Dispatching...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4" /> Dispatch via Twilio
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          HERO BANNER & PROBLEM STATEMENT 1 HEADER
      ───────────────────────────────────────────────────────────── */}
      <section className="relative border-b border-gray-800 bg-[radial-gradient(ellipse_70%_80%_at_50%_0%,rgba(245,158,11,0.12)_0%,transparent_100%)]">
        <div className="box-border mx-auto w-[1300px] max-w-full px-5 lg:px-16 py-12">
          <div className="flex flex-wrap items-center gap-3 font-mono text-xs uppercase tracking-wider text-textmuted mb-3">
            <span className="inline-flex items-center gap-1.5 rounded-md border border-accent/30 bg-accent/10 px-2.5 py-1 font-semibold text-accent">
              <Sparkles className="w-3.5 h-3.5" /> Problem Statement 1
            </span>
            <span className="text-gray-600">•</span>
            <span>Discovering Hidden Industrial Symbiosis</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-bold tracking-tight text-white max-w-4xl">
            Industrial Symbiosis <span className="text-accent">Opportunity Engine</span>
          </h1>
          <p className="mt-3 text-sm sm:text-base text-textmuted max-w-3xl leading-relaxed">
            AI-powered material analysis + W2RKG Knowledge Graph matching. Evaluates 9 transparent opportunity factors
            including material, quantity, quality, timing, logistics, and net environmental benefits.
          </p>

          {/* Quick Presets */}
          <div className="mt-6 flex flex-wrap items-center gap-2">
            <span className="text-xs font-mono uppercase tracking-wider text-textmuted mr-2">Benchmarks:</span>
            {presets.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handleApplyPreset(p)}
                className="text-xs font-mono px-3 py-1.5 rounded-full border border-gray-700 bg-secondary hover:border-accent hover:text-accent transition-all text-textmain/90"
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          MAIN WORKBENCH: AI MATERIAL ANALYZER + OPPORTUNITY DISCOVERY
      ───────────────────────────────────────────────────────────── */}
      <div className="box-border mx-auto w-[1300px] max-w-full px-5 lg:px-16 mt-8 space-y-8">
        {/* Module 1: AI Natural Language Waste / Property Analyzer Card */}
        <div className="bg-secondary/70 border border-gray-800 rounded-2xl p-6 backdrop-blur-sm shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3 pb-3 border-b border-gray-800">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-accent" />
              <h2 className="text-lg font-bold text-white">AI Material & Property Analyzer</h2>
            </div>
            <span className="text-xs font-mono text-textmuted">Natural Language Extraction & Verification</span>
          </div>

          <div className="flex flex-col md:flex-row gap-3">
            <input
              type="text"
              value={rawTextPrompt}
              onChange={(e) => setRawTextPrompt(e.target.value)}
              placeholder="e.g. We generate 5000 kg of fly ash every month with 8% moisture in Mumbai."
              className="flex-1 bg-primary border border-gray-700 rounded-xl p-3 text-sm text-white focus:border-accent focus:outline-none"
            />
            <button
              onClick={handleExtractMaterial}
              disabled={extractingMaterial}
              className="bg-accent text-primary font-bold px-6 py-3 rounded-xl hover:bg-orange-500 transition-all flex items-center justify-center gap-2 text-sm whitespace-nowrap disabled:opacity-50"
            >
              {extractingMaterial ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Structuring...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" /> Extract & Analyze Material
                </>
              )}
            </button>
          </div>

          {/* Structured Material Profile Preview */}
          {extractedProfile && (
            <div className="mt-4 p-4 bg-primary/90 border border-gray-800 rounded-xl space-y-3 animate-fade-in text-xs">
              <div className="flex justify-between items-center pb-2 border-b border-gray-800">
                <span className="font-bold text-white text-sm flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-emerald-400" />
                  Structured Material Profile: {extractedProfile.material_name}
                </span>
                <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 font-bold">
                  Category: {extractedProfile.material_category}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-2 bg-secondary rounded-lg">
                  <span className="text-textmuted text-[10px] uppercase font-mono block">Grade / Quality</span>
                  <span className="text-white font-medium">{extractedProfile.quality_grade}</span>
                </div>
                <div className="p-2 bg-secondary rounded-lg">
                  <span className="text-textmuted text-[10px] uppercase font-mono block">Moisture Content</span>
                  <span className="text-accent font-medium">
                    {extractedProfile.physical_properties?.moisture_content?.value || "N/A"}
                    {extractedProfile.physical_properties?.moisture_content?.is_inferred && (
                      <span className="text-[9px] text-gray-500 ml-1 font-mono">(inferred)</span>
                    )}
                  </span>
                </div>
                <div className="p-2 bg-secondary rounded-lg">
                  <span className="text-textmuted text-[10px] uppercase font-mono block">Supply Frequency</span>
                  <span className="text-white font-medium">{extractedProfile.availability_frequency}</span>
                </div>
                <div className="p-2 bg-secondary rounded-lg">
                  <span className="text-textmuted text-[10px] uppercase font-mono block">Recurring Cycle</span>
                  <span className="text-white font-medium">{extractedProfile.availability_window?.recurring_window}</span>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                <span className="text-[10px] uppercase font-mono text-textmuted mr-1">Verified Provided Fields:</span>
                {extractedProfile.metadata?.provided_fields?.map((f, i) => (
                  <span key={i} className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    ✓ {f.replace("physical_properties.", "")}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ─────────────────────────────────────────────────────────────
            MODULE 2: MULTI-INDUSTRY FILTER & OPPORTUNITY DASHBOARD
        ───────────────────────────────────────────────────────────── */}
        <div className="flex flex-wrap items-center justify-between gap-4 pb-2 border-b border-gray-800">
          <div>
            <h3 className="text-xl font-bold text-white">Discovered Industrial Opportunities</h3>
            <p className="text-xs text-textmuted mt-0.5">
              Showing cross-sector opportunities ranked by transparent Opportunity Scores.
            </p>
          </div>

          {/* Industry Category Filter Pills */}
          <div className="flex flex-wrap gap-1.5">
            {industryFilters.map((ind) => (
              <button
                key={ind}
                onClick={() => setSelectedIndustryFilter(ind)}
                className={`text-xs font-mono px-3 py-1 rounded-lg transition-all ${
                  selectedIndustryFilter === ind
                    ? "bg-accent text-primary font-bold shadow-md"
                    : "bg-secondary border border-gray-800 text-textmuted hover:text-white"
                }`}
              >
                {ind}
              </button>
            ))}
          </div>
        </div>

        {/* W2RKG Interactive Graph */}
        {analysisResult?.networkGraph && (
          <SymbiosisNetworkGraph data={analysisResult.networkGraph} />
        )}

        {/* Opportunity Cards List */}
        {loading ? (
          <div className="bg-secondary/40 border border-gray-800 rounded-2xl p-16 text-center space-y-4">
            <RefreshCw className="w-10 h-10 animate-spin text-accent mx-auto" />
            <h4 className="text-xl font-bold text-white">Evaluating 9-Factor Industrial Feasibility...</h4>
          </div>
        ) : (
          <div className="space-y-6">
            {filteredPartners.length === 0 ? (
              <div className="bg-secondary/40 border border-gray-800 rounded-xl p-8 text-center text-textmuted">
                No matching opportunities found for industry filter "{selectedIndustryFilter}".
              </div>
            ) : (
              filteredPartners.map((partner, idx) => (
                <div
                  key={idx}
                  className="bg-secondary/80 border border-gray-800 hover:border-purple-500/60 rounded-2xl p-6 transition-all space-y-5 shadow-xl group"
                >
                  {/* Top Header */}
                  <div className="flex flex-col sm:flex-row justify-between sm:items-start gap-4">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="text-2xl font-bold text-white group-hover:text-purple-300 transition-colors">
                          {partner.industry.company_name}
                        </h4>
                        <span className="bg-purple-500/10 text-purple-400 border border-purple-500/30 text-xs font-mono px-2.5 py-0.5 rounded-full font-semibold">
                          Sector: {partner.industry.industry_type}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-textmuted mt-1.5 flex-wrap">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-gray-500" /> {partner.industry.location}
                        </span>
                        <span>•</span>
                        <span>{partner.distance} km away</span>
                        <span>•</span>
                        <span className="text-emerald-400 font-mono">
                          Demands: {partner.transformationPathway.transformed_resource}
                        </span>
                      </div>
                    </div>

                    {/* Overall Opportunity Score Badge */}
                    <div className="flex items-center gap-3 bg-primary/90 px-4 py-2.5 rounded-xl border border-purple-500/30 self-start">
                      <div className="text-right">
                        <div className="text-[10px] uppercase font-mono tracking-wider text-textmuted">
                          Opportunity Score
                        </div>
                        <div className="text-3xl font-bold font-mono text-purple-400 leading-none mt-0.5">
                          {partner.opportunityScore}%
                        </div>
                      </div>
                      <div className="w-10 h-10 rounded-full border-2 border-purple-500/40 bg-purple-500/10 flex items-center justify-center font-mono font-bold text-purple-400 text-xs">
                        #{idx + 1}
                      </div>
                    </div>
                  </div>

                  {/* Multi-Factor Overview Strip */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-primary/60 p-3.5 rounded-xl border border-gray-800 text-xs">
                    <div>
                      <span className="text-textmuted text-[10px] uppercase font-mono block">Timing Status</span>
                      <span className="font-semibold text-blue-400">{partner.timing_analysis?.status}</span>
                    </div>
                    <div>
                      <span className="text-textmuted text-[10px] uppercase font-mono block">Transport Cost</span>
                      <span className="font-semibold text-accent font-mono">
                        ₹{partner.logistics_analysis?.estimated_transport_cost_inr?.toLocaleString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-textmuted text-[10px] uppercase font-mono block">Preprocessing</span>
                      <span className="font-semibold text-white">
                        {partner.processing_analysis?.processing_complexity} Complexity
                      </span>
                    </div>
                    <div>
                      <span className="text-textmuted text-[10px] uppercase font-mono block">Net CO₂e Saved</span>
                      <span className="font-semibold text-green-400 font-mono">
                        {partner.environmentalImpact?.net_co2_saved_tonnes} tonnes
                      </span>
                    </div>
                  </div>

                  {/* Why this is an opportunity summary */}
                  <p className="text-xs text-textmain/90 leading-relaxed bg-primary/40 p-3 rounded-xl border border-gray-800">
                    <strong className="text-accent uppercase font-mono mr-1.5">Opportunity Evidence:</strong>
                    {partner.summary_reasoning}
                  </p>

                  {/* Actions Row */}
                  <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3 pt-3 border-t border-gray-800">
                    <button
                      onClick={() => setReasoningModal({ show: true, partner, activeTab: "overview" })}
                      className="text-xs font-mono text-accent hover:text-orange-400 flex items-center gap-1 font-semibold underline-offset-4 hover:underline"
                    >
                      <Info className="w-4 h-4" /> Why is this a potential symbiosis opportunity? (View 9-Factor Evidence)
                    </button>

                    <div className="flex items-center gap-2 flex-wrap">
                      <button
                        onClick={() => openTwilioModal(partner, "sms")}
                        className="bg-secondary border border-gray-700 hover:border-accent text-white px-3.5 py-2 rounded-xl text-xs font-mono flex items-center gap-1.5 transition-all"
                      >
                        <MessageSquare className="w-3.5 h-3.5 text-accent" /> SMS
                      </button>
                      <button
                        onClick={() => openTwilioModal(partner, "whatsapp")}
                        className="bg-secondary border border-gray-700 hover:border-green-500 text-white px-3.5 py-2 rounded-xl text-xs font-mono flex items-center gap-1.5 transition-all"
                      >
                        <MessageCircle className="w-3.5 h-3.5 text-green-500" /> WhatsApp
                      </button>
                      <button
                        onClick={() => openTwilioModal(partner, "voice")}
                        className="bg-secondary border border-gray-700 hover:border-purple-500 text-white px-3.5 py-2 rounded-xl text-xs font-mono flex items-center gap-1.5 transition-all"
                      >
                        <Phone className="w-3.5 h-3.5 text-purple-400" /> Call
                      </button>
                      <button
                        onClick={() => openTwilioModal(partner, "sms")}
                        className="bg-green-600 hover:bg-green-500 text-white font-bold px-4 py-2 rounded-xl text-xs flex items-center gap-1.5 transition-all shadow-md"
                      >
                        <Send className="w-3.5 h-3.5" /> Propose Partnership
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
