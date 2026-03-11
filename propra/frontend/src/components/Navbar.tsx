import { Link, useLocation } from "react-router-dom";
import { Scale, Menu, X } from "lucide-react";
import { useState } from "react";

const Navbar = () => {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const links = [
    { to: "/", label: "Home" },
    { to: "/advisor", label: "AI Advisor" },
    { to: "/permits", label: "Permit Process" },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-navy/95 backdrop-blur-sm border-b border-gold/20">
      <div className="container mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded bg-gold/20 border border-gold/40 flex items-center justify-center group-hover:bg-gold/30 transition-colors">
            <Scale className="w-4 h-4 text-gold" />
          </div>
          <span className="font-display font-bold text-primary-foreground text-lg tracking-tight">
            Recht<span className="text-gold">Immobilien</span>
          </span>
        </Link>

        {/* Desktop */}
        <div className="hidden md:flex items-center gap-1">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={`px-4 py-2 rounded text-sm font-body font-medium transition-all ${
                location.pathname === l.to
                  ? "bg-gold/20 text-gold"
                  : "text-primary-foreground/70 hover:text-primary-foreground hover:bg-white/5"
              }`}
            >
              {l.label}
            </Link>
          ))}
          <Link
            to="/advisor"
            className="ml-4 px-4 py-2 rounded bg-gold text-accent-foreground text-sm font-medium font-body hover:bg-gold-light transition-colors shadow-gold"
          >
            Ask a Question
          </Link>
        </div>

        {/* Mobile */}
        <button
          className="md:hidden text-primary-foreground/70 hover:text-primary-foreground"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {mobileOpen && (
        <div className="md:hidden bg-navy border-t border-gold/20 py-4 px-6 flex flex-col gap-2">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              onClick={() => setMobileOpen(false)}
              className={`px-4 py-2 rounded text-sm font-body font-medium transition-all ${
                location.pathname === l.to
                  ? "bg-gold/20 text-gold"
                  : "text-primary-foreground/70 hover:text-primary-foreground"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
};

export default Navbar;
