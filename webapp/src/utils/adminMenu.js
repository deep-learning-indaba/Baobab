import React, { useState, useRef, useEffect } from 'react';

export const AdminMenu = (props) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <li className="nav-item relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="nav-link bg-transparent border-0 flex items-center gap-1.5 focus:outline-none cursor-pointer"
      >
        {props.t(props.label)}
        <i className="fas fa-chevron-down" style={{ fontSize: 11 }} />
      </button>
      {isOpen && (
        <div 
          className="absolute left-0 mt-1 w-56 rounded-xl shadow-lg bg-white border border-border py-1 z-50 origin-top-left flex flex-col"
          onClick={() => setIsOpen(false)} // close when an item is clicked
        >
          {/* We wrap children to apply tailwind classes to NavLinks inside */}
          <div className="[&>a]:block [&>a]:px-4 [&>a]:py-2 [&>a]:text-sm [&>a]:text-foreground [&>a]:hover:bg-surface-low [&>a]:transition-colors">
            {props.children}
          </div>
        </div>
      )}
    </li>
  );
}
