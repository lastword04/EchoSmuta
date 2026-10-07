export const adaptResourceForCard = (resource) => {
  if (!resource) return null;
  
  return {
    name: resource.resource_name || resource.name || 'Ресурс',
    slug: resource.resource_slug || resource.slug || '',
    price: resource.price ?? 0,
    weight: resource.weight ?? 0,
  };
};