import React from 'react';

export const AdminMenu = (props) => {
	return (
		<li className="nav-item dropdown">
			<div
				className="nav-link dropdown-toggle"
				id="navbarDropdown"
				role="button"
				data-toggle="dropdown"
				aria-haspopup="true"
				aria-expanded="false"
			>
				{props.t(props.label)}
			</div>
			<div className="dropdown-menu" aria-labelledby="navbarDropdown">
				{props.children}
			</div>
		</li>
	)
}
