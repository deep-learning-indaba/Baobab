import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export const createColClassName = (xs, sm, md, lg) => {
  let colClassName = `col-${xs}  col-sm-${sm} col-md-${md} col-lg-${lg}`;
  return colClassName;
};

export const cn = (...inputs) => twMerge(clsx(inputs));
