import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

const resources = {
  es: {
    translation: {
      app: {
        name: 'MisFigus',
        tagline: 'Intercambia figuritas con tu álbum',
        defaultUser: 'Usuario'
      },
      login: {
        title: 'MisFigus',
        subtitle: 'Intercambia figuritas con tu álbum',
        emailPlaceholder: 'Tu correo electrónico',
        sendOTP: 'Enviar código',
        otpPlaceholder: 'Código de 6 dígitos',
        verify: 'Verificar',
        resend: 'Reenviar código',
        devMode: 'MODO DEV - Código OTP',
        devNote: 'Solo para pruebas. Revisa los logs del backend para más detalles.'
      },
      albums: {
        title: 'Mis Álbumes',
        select: 'Selecciona un álbum',
        active: 'ACTIVO',
        inactive: 'INACTIVO',
        comingSoon: 'PRÓXIMAMENTE',
        noAlbums: 'No hay álbumes disponibles',
        activate: 'Activar álbum',
        activateQuestion: '¿Querés activar este álbum?',
        activateConfirm: 'Activar',
        activateSuccess: 'Álbum activado correctamente',
        activateError: 'Error al activar el álbum',
        deactivate: 'Desactivar álbum',
        deactivateQuestion: 'Podrás volver a activarlo cuando quieras. Tu inventario no se borra.',
        deactivateConfirm: 'Desactivar',
        deactivateSuccess: 'Álbum desactivado correctamente'
      },
      albumHome: {
        members: 'Miembros',
        member: 'miembro',
        memberPlural: 'miembros',
        myInventory: 'Mi Inventario',
        duplicates: 'Duplicados',
        matches: 'Intercambios',
        offers: 'Ofertas',
        invite: 'Invitar',
        progress: 'Progreso',
        completed: 'completado',
        manageInventory: 'Gestiona tus figuritas, duplicados y faltantes',
        findTrades: 'Encuentra intercambios con otros coleccionistas',
        joinedSuccess: 'Te has unido al álbum',
        noStickersYet: 'Figuritas próximamente',
        noOtherMembers: 'Todavía no hay otros miembros en este álbum',
        placeholderBanner: 'Colección en preparación: por ahora usá numeración'
      },
      invite: {
        title: 'Invitar al Álbum',
        subtitle: 'Comparte este enlace con quien quieras invitar',
        generate: 'Generar Link de Invitación',
        copy: 'Copiar Link',
        select: 'Seleccionar Link',
        openTab: 'Abrir en Nueva Pestaña',
        copied: '¡Link copiado!',
        expires: 'Expira en 1 hora',
        singleUse: 'Uso único',
        accept: 'Aceptar Invitación',
        accepting: 'Aceptando...',
        expired: 'Este enlace ha expirado',
        used: 'Este enlace ya fue usado',
        invalid: 'Enlace inválido',
        loginFirst: 'Inicia sesión para aceptar la invitación'
      },
      inventory: {
        title: 'Mi Inventario',
        search: 'Buscar figuritas...',
        all: 'Todos',
        missing: 'Faltan',
        have: 'Tengo',
        duplicates: 'Duplicados',
        owned: 'Tengo',
        duplicate: 'Duplicado',
        noDuplicates: 'No tienes duplicados todavía',
        noStickers: 'No se encontraron figuritas'
      },
      matches: {
        title: 'Intercambios Sugeridos',
        youGive: 'Das',
        youGet: 'Recibes',
        noMatches: 'No hay intercambios disponibles',
        updateInventory: 'Actualiza tu inventario para encontrar intercambios',
        netGain: 'Ganas'
      },
      offers: {
        title: 'Ofertas',
        sent: 'Enviadas',
        received: 'Recibidas',
        accept: 'Aceptar',
        reject: 'Rechazar',
        sticker: 'Figurita',
        status: {
          sent: 'Enviada',
          accepted: 'Aceptada',
          rejected: 'Rechazada'
        }
      },
      settings: {
        title: 'Configuración',
        language: 'Idioma',
        spanish: 'Español',
        english: 'English',
        portuguese: 'Português',
        french: 'Français',
        german: 'Deutsch',
        italian: 'Italiano',
        logout: 'Cerrar Sesión',
        profile: 'Mi Perfil'
      },
      profile: {
        title: 'Mi Perfil',
        displayName: 'Nombre y apellido',
        displayNamePlaceholder: 'Ejemplo: Juan Pérez',
        email: 'Correo electrónico',
        save: 'Guardar cambios',
        saved: 'Perfil actualizado correctamente',
        helperText: 'Este nombre se mostrará a otros miembros del álbum'
      },
      members: {
        title: 'Miembros',
        viewAll: 'Ver todos',
        creator: 'Creador',
        member: 'Miembro',
        testUser: 'Usuario de prueba',
        newTestUser: 'Nuevo usuario (prueba)',
        technicalAccount: 'Cuenta técnica (prueba)'
      },
      common: {
        loading: 'Cargando...',
        error: 'Error',
        success: 'Éxito',
        back: 'Volver',
        close: 'Cerrar',
        cancel: 'Cancelar',
        save: 'Guardar',
        delete: 'Eliminar',
        edit: 'Editar'
      }
    }
  },
  en: {
    translation: {
      app: {
        name: 'MisFigus',
        tagline: 'Trade stickers with your album',
        defaultUser: 'User'
      },
      login: {
        title: 'MisFigus',
        subtitle: 'Trade stickers with your album',
        emailPlaceholder: 'Your email',
        sendOTP: 'Send Code',
        otpPlaceholder: '6-digit code',
        verify: 'Verify',
        resend: 'Resend Code',
        devMode: 'DEV MODE - OTP Code',
        devNote: 'Testing only. Check backend logs for details.'
      },
      albums: {
        title: 'My Albums',
        select: 'Select an album',
        active: 'ACTIVE',
        inactive: 'INACTIVE',
        comingSoon: 'COMING SOON',
        noAlbums: 'No albums available',
        activate: 'Activate album',
        activateQuestion: 'Do you want to activate this album?',
        activateConfirm: 'Activate',
        activateSuccess: 'Album activated successfully',
        activateError: 'Error activating album',
        deactivate: 'Deactivate album',
        deactivateQuestion: 'You can reactivate it anytime. Your inventory will not be deleted.',
        deactivateConfirm: 'Deactivate',
        deactivateSuccess: 'Album deactivated successfully'
      },
      albumHome: {
        members: 'Members',
        member: 'member',
        memberPlural: 'members',
        myInventory: 'My Inventory',
        duplicates: 'Duplicates',
        matches: 'Trades',
        offers: 'Offers',
        invite: 'Invite',
        progress: 'Progress',
        completed: 'completed',
        manageInventory: 'Manage your stickers, duplicates and missing',
        findTrades: 'Find trades with other collectors',
        joinedSuccess: 'You joined the album',
        noStickersYet: 'Stickers coming soon',
        noOtherMembers: 'No other members in this album yet',
        placeholderBanner: 'Collection in preparation: use numbering for now'
      },
      invite: {
        title: 'Invite to Album',
        subtitle: 'Share this link with who you want to invite',
        generate: 'Generate Invite Link',
        copy: 'Copy Link',
        select: 'Select Link',
        openTab: 'Open in New Tab',
        copied: 'Link copied!',
        expires: 'Expires in 1 hour',
        singleUse: 'Single use',
        accept: 'Accept Invitation',
        accepting: 'Accepting...',
        expired: 'This link has expired',
        used: 'This link has already been used',
        invalid: 'Invalid link',
        loginFirst: 'Login to accept the invitation'
      },
      inventory: {
        title: 'My Inventory',
        search: 'Search stickers...',
        all: 'All',
        missing: 'Missing',
        have: 'Have',
        duplicates: 'Duplicates',
        owned: 'Owned',
        duplicate: 'Duplicate',
        noDuplicates: 'No duplicates yet',
        noStickers: 'No stickers found'
      },
      matches: {
        title: 'Suggested Trades',
        youGive: 'You Give',
        youGet: 'You Get',
        noMatches: 'No trades available',
        updateInventory: 'Update your inventory to find trades',
        netGain: 'You Gain'
      },
      offers: {
        title: 'Offers',
        sent: 'Sent',
        received: 'Received',
        accept: 'Accept',
        reject: 'Reject',
        sticker: 'Sticker',
        status: {
          sent: 'Sent',
          accepted: 'Accepted',
          rejected: 'Rejected'
        }
      },
      settings: {
        title: 'Settings',
        language: 'Language',
        spanish: 'Español',
        english: 'English',
        portuguese: 'Português',
        french: 'Français',
        german: 'Deutsch',
        italian: 'Italiano',
        logout: 'Logout',
        profile: 'My Profile'
      },
      profile: {
        title: 'My Profile',
        displayName: 'Full name',
        displayNamePlaceholder: 'Example: John Smith',
        email: 'Email',
        save: 'Save changes',
        saved: 'Profile updated successfully',
        helperText: 'This name will be shown to other album members'
      },
      members: {
        title: 'Members',
        viewAll: 'View all',
        creator: 'Creator',
        member: 'Member',
        testUser: 'Test user',
        newTestUser: 'New test user',
        technicalAccount: 'Technical account (test)'
      },
      common: {
        loading: 'Loading...',
        error: 'Error',
        success: 'Success',
        back: 'Back',
        close: 'Close',
        cancel: 'Cancel',
        save: 'Save',
        delete: 'Delete',
        edit: 'Edit'
      }
    }
  },
  pt: {
    translation: {
      app: {
        name: 'MisFigus',
        tagline: 'Troque figurinhas com seu álbum',
        defaultUser: 'Usuário'
      },
      login: {
        title: 'MisFigus',
        subtitle: 'Troque figurinhas com seu álbum',
        emailPlaceholder: 'Seu e-mail',
        sendOTP: 'Enviar código',
        otpPlaceholder: 'Código de 6 dígitos',
        verify: 'Verificar',
        resend: 'Reenviar código',
        devMode: 'MODO DEV - Código OTP',
        devNote: 'Apenas para testes. Verifique os logs do backend para detalhes.'
      },
      albums: {
        title: 'Meus Álbuns',
        select: 'Selecione um álbum',
        active: 'ATIVO',
        inactive: 'INATIVO',
        comingSoon: 'EM BREVE',
        noAlbums: 'Nenhum álbum disponível',
        activate: 'Ativar álbum',
        activateQuestion: 'Você quer ativar este álbum?',
        activateConfirm: 'Ativar',
        activateSuccess: 'Álbum ativado com sucesso',
        activateError: 'Erro ao ativar o álbum',
        deactivate: 'Desativar álbum',
        deactivateQuestion: 'Você pode reativá-lo quando quiser. Seu inventário não será apagado.',
        deactivateConfirm: 'Desativar',
        deactivateSuccess: 'Álbum desativado com sucesso'
      },
      albumHome: {
        members: 'Membros',
        member: 'membro',
        memberPlural: 'membros',
        myInventory: 'Meu Inventário',
        duplicates: 'Duplicadas',
        matches: 'Trocas',
        offers: 'Ofertas',
        invite: 'Convidar',
        progress: 'Progresso',
        completed: 'completo',
        manageInventory: 'Gerencie suas figurinhas, duplicadas e faltantes',
        findTrades: 'Encontre trocas com outros colecionadores',
        joinedSuccess: 'Você entrou no álbum',
        noStickersYet: 'Figurinhas em breve',
        noOtherMembers: 'Ainda não há outros membros neste álbum',
        placeholderBanner: 'Coleção em preparação: use numeração por enquanto'
      },
      invite: {
        title: 'Convidar para o Álbum',
        subtitle: 'Compartilhe este link com quem você quer convidar',
        generate: 'Gerar Link de Convite',
        copy: 'Copiar Link',
        select: 'Selecionar Link',
        openTab: 'Abrir em Nova Aba',
        copied: 'Link copiado!',
        expires: 'Expira em 1 hora',
        singleUse: 'Uso único',
        accept: 'Aceitar Convite',
        accepting: 'Aceitando...',
        expired: 'Este link expirou',
        used: 'Este link já foi usado',
        invalid: 'Link inválido',
        loginFirst: 'Faça login para aceitar o convite'
      },
      inventory: {
        title: 'Meu Inventário',
        search: 'Buscar figurinhas...',
        all: 'Todas',
        missing: 'Faltando',
        have: 'Tenho',
        duplicates: 'Duplicadas',
        owned: 'Tenho',
        duplicate: 'Duplicada',
        noDuplicates: 'Nenhuma duplicada ainda',
        noStickers: 'Nenhuma figurinha encontrada'
      },
      matches: {
        title: 'Trocas Sugeridas',
        youGive: 'Você Dá',
        youGet: 'Você Recebe',
        noMatches: 'Nenhuma troca disponível',
        updateInventory: 'Atualize seu inventário para encontrar trocas',
        netGain: 'Você Ganha'
      },
      offers: {
        title: 'Ofertas',
        sent: 'Enviadas',
        received: 'Recebidas',
        accept: 'Aceitar',
        reject: 'Rejeitar',
        sticker: 'Figurinha',
        status: {
          sent: 'Enviada',
          accepted: 'Aceita',
          rejected: 'Rejeitada'
        }
      },
      settings: {
        title: 'Configurações',
        language: 'Idioma',
        spanish: 'Español',
        english: 'English',
        portuguese: 'Português',
        french: 'Français',
        german: 'Deutsch',
        italian: 'Italiano',
        logout: 'Sair',
        profile: 'Meu Perfil'
      },
      profile: {
        title: 'Meu Perfil',
        displayName: 'Nome completo',
        displayNamePlaceholder: 'Exemplo: João Silva',
        email: 'E-mail',
        save: 'Salvar alterações',
        saved: 'Perfil atualizado com sucesso',
        helperText: 'Este nome será mostrado aos outros membros do álbum'
      },
      members: {
        title: 'Membros',
        viewAll: 'Ver todos',
        creator: 'Criador',
        member: 'Membro',
        testUser: 'Usuário de teste',
        newTestUser: 'Novo usuário (teste)',
        technicalAccount: 'Conta técnica (teste)'
      },
      common: {
        loading: 'Carregando...',
        error: 'Erro',
        success: 'Sucesso',
        back: 'Voltar',
        close: 'Fechar',
        cancel: 'Cancelar',
        save: 'Salvar',
        delete: 'Excluir',
        edit: 'Editar'
      }
    }
  },
  fr: {
    translation: {
      app: {
        name: 'MisFigus',
        tagline: 'Échangez des autocollants avec votre album',
        defaultUser: 'Utilisateur'
      },
      login: {
        title: 'MisFigus',
        subtitle: 'Échangez des autocollants avec votre album',
        emailPlaceholder: 'Votre e-mail',
        sendOTP: 'Envoyer le code',
        otpPlaceholder: 'Code à 6 chiffres',
        verify: 'Vérifier',
        resend: 'Renvoyer le code',
        devMode: 'MODE DEV - Code OTP',
        devNote: 'Tests uniquement. Vérifiez les logs backend pour plus de détails.'
      },
      albums: {
        title: 'Mes Albums',
        select: 'Sélectionnez un album',
        active: 'ACTIF',
        inactive: 'INACTIF',
        comingSoon: 'PROCHAINEMENT',
        noAlbums: 'Aucun album disponible',
        activate: 'Activer l\'album',
        activateQuestion: 'Voulez-vous activer cet album?',
        activateConfirm: 'Activer',
        activateSuccess: 'Album activé avec succès',
        activateError: 'Erreur lors de l\'activation de l\'album',
        deactivate: 'Désactiver l\'album',
        deactivateQuestion: 'Vous pouvez le réactiver à tout moment. Votre inventaire ne sera pas supprimé.',
        deactivateConfirm: 'Désactiver',
        deactivateSuccess: 'Album désactivé avec succès'
      },
      albumHome: {
        members: 'Membres',
        member: 'membre',
        memberPlural: 'membres',
        myInventory: 'Mon Inventaire',
        duplicates: 'Doublons',
        matches: 'Échanges',
        offers: 'Offres',
        invite: 'Inviter',
        progress: 'Progrès',
        completed: 'complété',
        manageInventory: 'Gérez vos autocollants, doublons et manquants',
        findTrades: 'Trouvez des échanges avec d\'autres collectionneurs',
        joinedSuccess: 'Vous avez rejoint l\'album',
        noStickersYet: 'Autocollants à venir',
        noOtherMembers: 'Aucun autre membre dans cet album pour le moment',
        placeholderBanner: 'Collection en préparation: utilisez la numérotation pour l\'instant'
      },
      invite: {
        title: 'Inviter à l\'Album',
        subtitle: 'Partagez ce lien avec qui vous voulez inviter',
        generate: 'Générer un Lien d\'Invitation',
        copy: 'Copier le Lien',
        select: 'Sélectionner le Lien',
        openTab: 'Ouvrir dans un Nouvel Onglet',
        copied: 'Lien copié!',
        expires: 'Expire dans 1 heure',
        singleUse: 'Usage unique',
        accept: 'Accepter l\'Invitation',
        accepting: 'Acceptation...',
        expired: 'Ce lien a expiré',
        used: 'Ce lien a déjà été utilisé',
        invalid: 'Lien invalide',
        loginFirst: 'Connectez-vous pour accepter l\'invitation'
      },
      inventory: {
        title: 'Mon Inventaire',
        search: 'Rechercher des autocollants...',
        all: 'Tous',
        missing: 'Manquants',
        have: 'Possédés',
        duplicates: 'Doublons',
        owned: 'Possédé',
        duplicate: 'Doublon',
        noDuplicates: 'Aucun doublon pour le moment',
        noStickers: 'Aucun autocollant trouvé'
      },
      matches: {
        title: 'Échanges Suggérés',
        youGive: 'Vous Donnez',
        youGet: 'Vous Recevez',
        noMatches: 'Aucun échange disponible',
        updateInventory: 'Mettez à jour votre inventaire pour trouver des échanges',
        netGain: 'Vous Gagnez'
      },
      offers: {
        title: 'Offres',
        sent: 'Envoyées',
        received: 'Reçues',
        accept: 'Accepter',
        reject: 'Rejeter',
        sticker: 'Autocollant',
        status: {
          sent: 'Envoyée',
          accepted: 'Acceptée',
          rejected: 'Rejetée'
        }
      },
      settings: {
        title: 'Paramètres',
        language: 'Langue',
        spanish: 'Español',
        english: 'English',
        portuguese: 'Português',
        french: 'Français',
        german: 'Deutsch',
        italian: 'Italiano',
        logout: 'Déconnexion',
        profile: 'Mon Profil'
      },
      profile: {
        title: 'Mon Profil',
        displayName: 'Nom complet',
        displayNamePlaceholder: 'Exemple: Jean Dupont',
        email: 'E-mail',
        save: 'Enregistrer les modifications',
        saved: 'Profil mis à jour avec succès',
        helperText: 'Ce nom sera affiché aux autres membres de l\'album'
      },
      members: {
        title: 'Membres',
        viewAll: 'Voir tout',
        creator: 'Créateur',
        member: 'Membre',
        testUser: 'Utilisateur de test',
        newTestUser: 'Nouvel utilisateur (test)',
        technicalAccount: 'Compte technique (test)'
      },
      common: {
        loading: 'Chargement...',
        error: 'Erreur',
        success: 'Succès',
        back: 'Retour',
        close: 'Fermer',
        cancel: 'Annuler',
        save: 'Enregistrer',
        delete: 'Supprimer',
        edit: 'Modifier'
      }
    }
  },
  de: {
    translation: {
      app: {
        name: 'MisFigus',
        tagline: 'Tausche Sticker mit deinem Album',
        defaultUser: 'Benutzer'
      },
      login: {
        title: 'MisFigus',
        subtitle: 'Tausche Sticker mit deinem Album',
        emailPlaceholder: 'Deine E-Mail',
        sendOTP: 'Code senden',
        otpPlaceholder: '6-stelliger Code',
        verify: 'Überprüfen',
        resend: 'Code erneut senden',
        devMode: 'DEV-MODUS - OTP-Code',
        devNote: 'Nur zum Testen. Überprüfe die Backend-Logs für Details.'
      },
      albums: {
        title: 'Meine Alben',
        select: 'Wähle ein Album',
        active: 'AKTIV',
        inactive: 'INAKTIV',
        comingSoon: 'BALD VERFÜGBAR',
        noAlbums: 'Keine Alben verfügbar',
        activate: 'Album aktivieren',
        activateQuestion: 'Möchtest du dieses Album aktivieren?',
        activateConfirm: 'Aktivieren',
        activateSuccess: 'Album erfolgreich aktiviert',
        activateError: 'Fehler beim Aktivieren des Albums',
        deactivate: 'Album deaktivieren',
        deactivateQuestion: 'Du kannst es jederzeit wieder aktivieren. Dein Inventar wird nicht gelöscht.',
        deactivateConfirm: 'Deaktivieren',
        deactivateSuccess: 'Album erfolgreich deaktiviert'
      },
      albumHome: {
        members: 'Mitglieder',
        member: 'Mitglied',
        memberPlural: 'Mitglieder',
        myInventory: 'Mein Inventar',
        duplicates: 'Duplikate',
        matches: 'Tausche',
        offers: 'Angebote',
        invite: 'Einladen',
        progress: 'Fortschritt',
        completed: 'abgeschlossen',
        manageInventory: 'Verwalte deine Sticker, Duplikate und fehlende',
        findTrades: 'Finde Tausche mit anderen Sammlern',
        joinedSuccess: 'Du bist dem Album beigetreten',
        noStickersYet: 'Sticker kommen bald',
        noOtherMembers: 'Noch keine anderen Mitglieder in diesem Album',
        placeholderBanner: 'Sammlung in Vorbereitung: verwende vorerst Nummerierung'
      },
      invite: {
        title: 'Zum Album Einladen',
        subtitle: 'Teile diesen Link mit wem du einladen möchtest',
        generate: 'Einladungslink Generieren',
        copy: 'Link Kopieren',
        select: 'Link Auswählen',
        openTab: 'In Neuem Tab Öffnen',
        copied: 'Link kopiert!',
        expires: 'Läuft in 1 Stunde ab',
        singleUse: 'Einmalige Verwendung',
        accept: 'Einladung Annehmen',
        accepting: 'Annehmen...',
        expired: 'Dieser Link ist abgelaufen',
        used: 'Dieser Link wurde bereits verwendet',
        invalid: 'Ungültiger Link',
        loginFirst: 'Melde dich an, um die Einladung anzunehmen'
      },
      inventory: {
        title: 'Mein Inventar',
        search: 'Sticker suchen...',
        all: 'Alle',
        missing: 'Fehlend',
        have: 'Besitzen',
        duplicates: 'Duplikate',
        owned: 'Besessen',
        duplicate: 'Duplikat',
        noDuplicates: 'Noch keine Duplikate',
        noStickers: 'Keine Sticker gefunden'
      },
      matches: {
        title: 'Vorgeschlagene Tausche',
        youGive: 'Du Gibst',
        youGet: 'Du Erhältst',
        noMatches: 'Keine Tausche verfügbar',
        updateInventory: 'Aktualisiere dein Inventar, um Tausche zu finden',
        netGain: 'Du Gewinnst'
      },
      offers: {
        title: 'Angebote',
        sent: 'Gesendet',
        received: 'Empfangen',
        accept: 'Annehmen',
        reject: 'Ablehnen',
        sticker: 'Sticker',
        status: {
          sent: 'Gesendet',
          accepted: 'Angenommen',
          rejected: 'Abgelehnt'
        }
      },
      settings: {
        title: 'Einstellungen',
        language: 'Sprache',
        spanish: 'Español',
        english: 'English',
        portuguese: 'Português',
        french: 'Français',
        german: 'Deutsch',
        italian: 'Italiano',
        logout: 'Abmelden',
        profile: 'Mein Profil'
      },
      profile: {
        title: 'Mein Profil',
        displayName: 'Vollständiger Name',
        displayNamePlaceholder: 'Beispiel: Max Mustermann',
        email: 'E-Mail',
        save: 'Änderungen speichern',
        saved: 'Profil erfolgreich aktualisiert',
        helperText: 'Dieser Name wird anderen Albummitgliedern angezeigt'
      },
      members: {
        title: 'Mitglieder',
        viewAll: 'Alle anzeigen',
        creator: 'Ersteller',
        member: 'Mitglied',
        testUser: 'Testbenutzer',
        newTestUser: 'Neuer Testbenutzer',
        technicalAccount: 'Technisches Konto (Test)'
      },
      common: {
        loading: 'Laden...',
        error: 'Fehler',
        success: 'Erfolg',
        back: 'Zurück',
        close: 'Schließen',
        cancel: 'Abbrechen',
        save: 'Speichern',
        delete: 'Löschen',
        edit: 'Bearbeiten'
      }
    }
  },
  it: {
    translation: {
      app: {
        name: 'MisFigus',
        tagline: 'Scambia figurine con il tuo album',
        defaultUser: 'Utente'
      },
      login: {
        title: 'MisFigus',
        subtitle: 'Scambia figurine con il tuo album',
        emailPlaceholder: 'La tua email',
        sendOTP: 'Invia codice',
        otpPlaceholder: 'Codice a 6 cifre',
        verify: 'Verifica',
        resend: 'Reinvia codice',
        devMode: 'MODALITÀ DEV - Codice OTP',
        devNote: 'Solo per test. Controlla i log del backend per i dettagli.'
      },
      albums: {
        title: 'I Miei Album',
        select: 'Seleziona un album',
        active: 'ATTIVO',
        inactive: 'INATTIVO',
        comingSoon: 'PROSSIMAMENTE',
        noAlbums: 'Nessun album disponibile',
        activate: 'Attiva album',
        activateQuestion: 'Vuoi attivare questo album?',
        activateConfirm: 'Attiva',
        activateSuccess: 'Album attivato con successo',
        activateError: 'Errore nell\'attivazione dell\'album',
        deactivate: 'Disattiva album',
        deactivateQuestion: 'Puoi riattivarlo in qualsiasi momento. Il tuo inventario non sarà eliminato.',
        deactivateConfirm: 'Disattiva',
        deactivateSuccess: 'Album disattivato con successo'
      },
      albumHome: {
        members: 'Membri',
        member: 'membro',
        memberPlural: 'membri',
        myInventory: 'Il Mio Inventario',
        duplicates: 'Doppioni',
        matches: 'Scambi',
        offers: 'Offerte',
        invite: 'Invita',
        progress: 'Progresso',
        completed: 'completato',
        manageInventory: 'Gestisci le tue figurine, doppioni e mancanti',
        findTrades: 'Trova scambi con altri collezionisti',
        joinedSuccess: 'Ti sei unito all\'album',
        noStickersYet: 'Figurine in arrivo',
        noOtherMembers: 'Nessun altro membro in questo album per ora',
        placeholderBanner: 'Collezione in preparazione: usa la numerazione per ora'
      },
      invite: {
        title: 'Invita all\'Album',
        subtitle: 'Condividi questo link con chi vuoi invitare',
        generate: 'Genera Link di Invito',
        copy: 'Copia Link',
        select: 'Seleziona Link',
        openTab: 'Apri in Nuova Scheda',
        copied: 'Link copiato!',
        expires: 'Scade tra 1 ora',
        singleUse: 'Uso singolo',
        accept: 'Accetta Invito',
        accepting: 'Accettazione...',
        expired: 'Questo link è scaduto',
        used: 'Questo link è già stato usato',
        invalid: 'Link non valido',
        loginFirst: 'Accedi per accettare l\'invito'
      },
      inventory: {
        title: 'Il Mio Inventario',
        search: 'Cerca figurine...',
        all: 'Tutte',
        missing: 'Mancanti',
        have: 'Possedute',
        duplicates: 'Doppioni',
        owned: 'Posseduta',
        duplicate: 'Doppione',
        noDuplicates: 'Nessun doppione ancora',
        noStickers: 'Nessuna figurina trovata'
      },
      matches: {
        title: 'Scambi Suggeriti',
        youGive: 'Tu Dai',
        youGet: 'Tu Ricevi',
        noMatches: 'Nessuno scambio disponibile',
        updateInventory: 'Aggiorna il tuo inventario per trovare scambi',
        netGain: 'Tu Guadagni'
      },
      offers: {
        title: 'Offerte',
        sent: 'Inviate',
        received: 'Ricevute',
        accept: 'Accetta',
        reject: 'Rifiuta',
        sticker: 'Figurina',
        status: {
          sent: 'Inviata',
          accepted: 'Accettata',
          rejected: 'Rifiutata'
        }
      },
      settings: {
        title: 'Impostazioni',
        language: 'Lingua',
        spanish: 'Español',
        english: 'English',
        portuguese: 'Português',
        french: 'Français',
        german: 'Deutsch',
        italian: 'Italiano',
        logout: 'Disconnetti',
        profile: 'Il Mio Profilo'
      },
      profile: {
        title: 'Il Mio Profilo',
        displayName: 'Nome completo',
        displayNamePlaceholder: 'Esempio: Mario Rossi',
        email: 'Email',
        save: 'Salva modifiche',
        saved: 'Profilo aggiornato con successo',
        helperText: 'Questo nome sarà mostrato agli altri membri dell\'album'
      },
      members: {
        title: 'Membri',
        viewAll: 'Vedi tutti',
        creator: 'Creatore',
        member: 'Membro',
        testUser: 'Utente di test',
        newTestUser: 'Nuovo utente (test)',
        technicalAccount: 'Account tecnico (test)'
      },
      common: {
        loading: 'Caricamento...',
        error: 'Errore',
        success: 'Successo',
        back: 'Indietro',
        close: 'Chiudi',
        cancel: 'Annulla',
        save: 'Salva',
        delete: 'Elimina',
        edit: 'Modifica'
      }
    }
  }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'es',
    lng: 'es',
    interpolation: {
      escapeValue: false
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage']
    }
  });

export default i18n;
