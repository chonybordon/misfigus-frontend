import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, Search, Plus, Minus } from 'lucide-react';

export const Inventory = () => {
  const { groupId, albumId } = useParams();
  const contextId = groupId || albumId; // Support both group and album routes
  const isGroupContext = !!groupId;
  const [stickers, setStickers] = useState([]);
  const [filteredStickers, setFilteredStickers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all');
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchInventory();
  }, [contextId]);

  useEffect(() => {
    applyFilters();
  }, [stickers, searchTerm, filter]);

  const fetchInventory = async () => {
    try {
      // Use group endpoint if groupId, otherwise album endpoint
      const endpoint = isGroupContext 
        ? `/groups/${contextId}/inventory`
        : `/inventory?album_id=${contextId}`;
      const response = await api.get(endpoint);
      setStickers(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = stickers;

    if (searchTerm) {
      filtered = filtered.filter(
        (s) =>
          s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          s.team.toLowerCase().includes(searchTerm.toLowerCase()) ||
          s.number.toString().includes(searchTerm)
      );
    }

    if (filter === 'missing') {
      filtered = filtered.filter((s) => s.owned_qty === 0);
    } else if (filter === 'have') {
      filtered = filtered.filter((s) => s.owned_qty >= 1);
    } else if (filter === 'duplicates') {
      // ONLY show stickers where owned_qty >= 2
      filtered = filtered.filter((s) => s.owned_qty >= 2);
    }

    setFilteredStickers(filtered);
  };

  const updateQuantity = async (stickerId, newQty) => {
    try {
      // Use group endpoint if groupId, otherwise album endpoint
      const endpoint = isGroupContext 
        ? `/groups/${contextId}/inventory`
        : '/inventory';
      const payload = isGroupContext
        ? { sticker_id: stickerId, owned_qty: Math.max(0, newQty) }
        : { sticker_id: stickerId, owned_qty: Math.max(0, newQty) };
      await api.put(endpoint, payload);
      setStickers((prev) =>
        prev.map((s) => {
          if (s.id === stickerId) {
            const updated_qty = Math.max(0, newQty);
            return {
              ...s,
              owned_qty: updated_qty,
              duplicate_count: Math.max(updated_qty - 1, 0)
            };
          }
          return s;
        })
      );
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    }
  };

  // Get back navigation path
  const getBackPath = () => {
    return isGroupContext ? `/groups/${contextId}` : `/albums/${contextId}`;
  };

  const getStickerClass = (sticker) => {
    if (sticker.owned_qty === 0) return 'sticker-card-missing';
    if (sticker.owned_qty === 1) return 'sticker-card-have';
    return 'sticker-card-duplicate';
  };

  const getDisplayValue = (sticker) => {
    // In "Duplicates" tab, show duplicate_count
    // In other tabs, show owned_qty
    if (filter === 'duplicates') {
      return sticker.duplicate_count;
    }
    return sticker.owned_qty;
  };

  const progress = stickers.length > 0 ? (stickers.filter((s) => s.owned_qty > 0).length / stickers.length) * 100 : 0;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-bold">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen sticker-album-pattern pb-20">
      <div className="max-w-7xl mx-auto p-6">
        <div className="flex items-center gap-4 mb-6">
          <Button
            data-testid="back-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate(getBackPath())}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1">
            <h1 className="text-3xl font-black tracking-tight text-primary">{t('inventory.title')}</h1>
            <p className="text-muted-foreground text-sm">
              {Math.round(progress)}% {t('albumHome.completed')}
            </p>
          </div>
        </div>

        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              data-testid="search-stickers-input"
              placeholder={t('inventory.search')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        <Tabs defaultValue="all" className="mb-6" onValueChange={setFilter}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger data-testid="filter-all" value="all">{t('inventory.all')}</TabsTrigger>
            <TabsTrigger data-testid="filter-missing" value="missing">{t('inventory.missing')}</TabsTrigger>
            <TabsTrigger data-testid="filter-have" value="have">{t('inventory.have')}</TabsTrigger>
            <TabsTrigger data-testid="filter-duplicates" value="duplicates">{t('inventory.duplicates')}</TabsTrigger>
          </TabsList>
        </Tabs>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4" data-testid="stickers-grid">
          {filteredStickers.map((sticker) => (
            <Card
              key={sticker.id}
              data-testid={`sticker-card-${sticker.id}`}
              className={`p-4 transition-all duration-300 ${getStickerClass(sticker)}`}
            >
              <div className="text-center mb-2">
                <div className="text-2xl font-black text-primary mb-1">#{sticker.number}</div>
                <div className="text-sm font-semibold line-clamp-2 h-10">{sticker.name}</div>
                <div className="text-xs text-muted-foreground mt-1">{sticker.team}</div>
              </div>
              <div className="flex items-center justify-between gap-2 mt-3">
                <Button
                  data-testid={`decrease-qty-btn-${sticker.id}`}
                  size="sm"
                  variant="outline"
                  className="h-8 w-8 p-0"
                  onClick={() => updateQuantity(sticker.id, sticker.owned_qty - 1)}
                  disabled={sticker.owned_qty === 0}
                >
                  <Minus className="h-4 w-4" />
                </Button>
                <div className="flex flex-col items-center">
                  <div className="text-xl font-bold min-w-[2rem] text-center" data-testid={`sticker-qty-${sticker.id}`}>
                    {getDisplayValue(sticker)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {filter === 'duplicates' ? t('inventory.duplicate') : t('inventory.owned')}
                  </div>
                </div>
                <Button
                  data-testid={`increase-qty-btn-${sticker.id}`}
                  size="sm"
                  variant="outline"
                  className="h-8 w-8 p-0"
                  onClick={() => updateQuantity(sticker.id, sticker.owned_qty + 1)}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </Card>
          ))}
        </div>

        {filteredStickers.length === 0 && (
          <div className="text-center py-20 text-muted-foreground">
            {stickers.length === 0 
              ? t('albumHome.noStickersYet')
              : filter === 'duplicates' 
              ? t('inventory.noDuplicates')
              : t('inventory.noStickers')}
          </div>
        )}
      </div>
    </div>
  );
};

export default Inventory;
